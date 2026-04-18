#!/usr/bin/env python3
"""
工业AI全链路管线：感知 → 预测 → 归因
SAM3(视觉) + SAM-Audio(声纹) + TimesFM(时序预测) + LLM(归因分析)

Usage:
  python pipeline.py run              # 运行完整管线（模拟数据）
  python pipeline.py run --llm        # 运行完整管线 + LLM归因（需API Key）
  python pipeline.py detect           # 仅运行感知层
  python pipeline.py predict          # 仅运行预测层
  python pipeline.py diagnose         # 仅运行归因层
  python pipeline.py serve --port 8770  # 启动API服务器
  python pipeline.py generate-data    # 生成模拟测试数据
"""

import argparse, json, os, sys, random, math, time
from datetime import datetime, timedelta
from pathlib import Path
BIGMODEL_KEY = os.getenv("BIGMODEL_API_KEY", "")
DATA_DIR = Path("/tmp/test_data")

# ══════════════════════════════════════════════════
# 真实缺陷数据集注册表 (Kaggle)
# 类别先验、图像数、分辨率均取自公开数据集元信息，
# 供感知层按真实分布进行抽样，使 demo 数据贴近产线。
# ══════════════════════════════════════════════════

# Real sample images live under docs/industrial-ai/samples/. Each entry below
# carries a `sample` dict with the static URL and a `bbox` in NATIVE image
# coordinates marking a visible defect (frontend remaps to SVG viewport).
# Image sources:
#   - NEU-DET samples: github.com/siddhartamukherjee/NEU-DET-Steel-Surface-Defect-Detection
#   - Casting samples: github.com/naxty/gcp-automated-quality-inspection
#   - Severstal sample cropped from github.com/shubacca/Severstal-Steel-Defect-Segmentation
SAMPLE_BASE = "/samples"

DATASETS = {
    # https://www.kaggle.com/c/severstal-steel-defect-detection
    "severstal": {
        "id": "severstal",
        "name": "Severstal Steel Defect Detection",
        "source": "Kaggle competition (Severstal, 2019)",
        "url": "https://www.kaggle.com/c/severstal-steel-defect-detection",
        "material": "hot-rolled steel coil",
        "resolution": [1600, 256],
        "total_images": 18074,
        "total_objects": 19958,
        "train_images": 12568,
        "test_images": 5506,
        "unlabeled_ratio": 0.63,
        # Only one clean raw strip is re-hostable (competition data is non-redistributable);
        # every defect class reuses this same image so the bounding boxes land on real pixels.
        "shared_sample": {"url": f"{SAMPLE_BASE}/severstal/sample_01.jpg",
                          "native_size": [1758, 256]},
        "classes": [
            # counts & prior from datasetninja.com/severstal
            {"type": "defect_1", "label": "Class 1 · pitting", "severity": "medium",
             "area_px": 180, "count": 3082, "prior": 0.154,
             "bbox": [310, 20, 120, 150]},
            {"type": "defect_2", "label": "Class 2 · inclusion", "severity": "high",
             "area_px": 140, "count": 321, "prior": 0.016,
             "bbox": [950, 100, 90, 110]},
            {"type": "defect_3", "label": "Class 3 · scale (majority)", "severity": "medium",
             "area_px": 420, "count": 14648, "prior": 0.734,
             "bbox": [300, 30, 480, 180]},
            {"type": "defect_4", "label": "Class 4 · large patch", "severity": "high",
             "area_px": 640, "count": 1907, "prior": 0.095,
             "bbox": [200, 40, 900, 160]},
        ],
        # fraction of real images that carry >=1 defect (19958 / 18074 ≈ 1.1, but ~6666 labelled)
        "p_any_defect": 0.37,
    },
    # https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database
    "neu": {
        "id": "neu",
        "name": "NEU-DET Surface Defect Database",
        "source": "Northeastern University (Song & Yan, 2013)",
        "url": "https://www.kaggle.com/datasets/kaustubhdikshit/neu-surface-defect-database",
        "material": "hot-rolled steel strip",
        "resolution": [200, 200],
        "total_images": 1800,
        "total_objects": 1800,
        "classes": [
            # balanced: 300 images per class — each backed by a real defect close-up.
            {"type": "crazing",        "label": "Crazing (cr)",        "severity": "medium", "area_px": 220, "count": 300, "prior": 1/6,
             "sample": {"url": f"{SAMPLE_BASE}/neu/crazing_1.jpg", "native_size": [200, 200]},
             "bbox": [20, 20, 160, 160]},
            {"type": "inclusion",      "label": "Inclusion (in)",      "severity": "high",   "area_px": 260, "count": 300, "prior": 1/6,
             "sample": {"url": f"{SAMPLE_BASE}/neu/inclusion_1.jpg", "native_size": [200, 200]},
             "bbox": [30, 40, 140, 130]},
            {"type": "patches",        "label": "Patches (pa)",        "severity": "medium", "area_px": 420, "count": 300, "prior": 1/6,
             "sample": {"url": f"{SAMPLE_BASE}/neu/patches_1.jpg", "native_size": [200, 200]},
             "bbox": [10, 10, 180, 180]},
            {"type": "pitted_surface", "label": "Pitted surface (ps)", "severity": "high",   "area_px": 320, "count": 300, "prior": 1/6,
             "sample": {"url": f"{SAMPLE_BASE}/neu/pitted_surface_1.jpg", "native_size": [200, 200]},
             "bbox": [20, 20, 160, 160]},
            {"type": "rolled_in_scale","label": "Rolled-in scale (rs)","severity": "medium", "area_px": 280, "count": 300, "prior": 1/6,
             "sample": {"url": f"{SAMPLE_BASE}/neu/rolled-in_scale_1.jpg", "native_size": [200, 200]},
             "bbox": [15, 20, 170, 160]},
            {"type": "scratches",      "label": "Scratches (sc)",      "severity": "low",    "area_px": 180, "count": 300, "prior": 1/6,
             "sample": {"url": f"{SAMPLE_BASE}/neu/scratches_1.jpg", "native_size": [200, 200]},
             "bbox": [30, 20, 60, 170]},
        ],
        # NEU-DET is defect-only (every image is a defect)
        "p_any_defect": 1.0,
    },
    # https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product
    "casting": {
        "id": "casting",
        "name": "Casting Product — Submersible Pump Impeller",
        "source": "Kaggle / Pilot Technocast (Ravirajsinh Dabhi, 2020)",
        "url": "https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product",
        "material": "aluminum submersible-pump impeller (top view)",
        "resolution": [300, 300],
        "total_images": 7348,
        "train_defective": 3758,
        "train_ok": 2875,
        "test_defective": 453,
        "test_ok": 262,
        "classes": [
            # 4211 defective / 7348 total ≈ 57.3%
            {"type": "def_front", "label": "Defective (blow-hole / burr / shrink)",
             "severity": "high", "area_px": 900, "count": 4211, "prior": 0.573,
             "sample": {"url": f"{SAMPLE_BASE}/casting/def_front.jpeg", "native_size": [300, 300]},
             "bbox": [150, 230, 110, 60]},
            {"type": "ok_front",  "label": "OK",
             "severity": "low",  "area_px": 0,   "count": 3137, "prior": 0.427,
             "sample": {"url": f"{SAMPLE_BASE}/casting/ok_front.jpeg", "native_size": [300, 300]},
             "bbox": None},
        ],
        # p_any_defect represents "frame shows a defective part"
        "p_any_defect": 0.573,
    },
}

DEFAULT_DATASET = "severstal"


def _dataset(name: str | None):
    return DATASETS.get(name or DEFAULT_DATASET, DATASETS[DEFAULT_DATASET])


def _sample_class(ds: dict) -> dict:
    """Weighted pick of a defect class honoring the dataset's real prior."""
    # Skip 'ok_front' when sampling a defect (its presence is controlled by p_any_defect).
    defect_classes = [c for c in ds["classes"] if c.get("type") != "ok_front"]
    weights = [c.get("prior", 1.0) for c in defect_classes]
    total = sum(weights) or 1.0
    r = random.random() * total
    acc = 0.0
    for c, w in zip(defect_classes, weights):
        acc += w
        if r <= acc:
            return dict(c)
    return dict(defect_classes[-1])


def _choose_frame(ds: dict, chosen_classes: list) -> dict:
    """Resolve which real sample image backs this frame."""
    # Severstal: single redistributable strip shared across all classes.
    if "shared_sample" in ds:
        return ds["shared_sample"]
    # Casting: OK frames use the ok_front sample, defective frames use def_front.
    if ds["id"] == "casting":
        key = "def_front" if chosen_classes else "ok_front"
        for c in ds["classes"]:
            if c["type"] == key and c.get("sample"):
                return c["sample"]
    # NEU: use the sampled class's own image, falling back to a random class.
    if chosen_classes and chosen_classes[0].get("sample"):
        return chosen_classes[0]["sample"]
    for c in ds["classes"]:
        if c.get("sample"):
            return c["sample"]
    # Last-resort: synthesise a placeholder frame at the dataset's nominal size.
    return {"url": None, "native_size": ds["resolution"]}


# ══════════════════════════════════════════════════
# Layer 1: 感知层 (SAM3 + SAM-Audio 模拟)
# ══════════════════════════════════════════════════

class PerceptionLayer:
    """模拟SAM3视觉检测 + SAM-Audio声纹分析"""

    # Legacy list kept for external importers; real data now comes from DATASETS.
    DEFECT_TYPES = [
        {"type": c["type"], "label": c["label"], "severity": c["severity"], "area_px": c["area_px"]}
        for c in DATASETS["severstal"]["classes"]
    ]

    AUDIO_ANOMALIES = [
        {"type": "bearing_wear", "label": "轴承磨损", "freq_hz": 1200, "confidence": 0.85},
        {"type": "air_leak", "label": "气泄漏", "freq_hz": 8500, "confidence": 0.92},
        {"type": "motor_imbalance", "label": "电机不平衡", "freq_hz": 50, "confidence": 0.78},
        {"type": "gear_mesh", "label": "齿轮啮合异常", "freq_hz": 3200, "confidence": 0.88},
    ]

    @staticmethod
    def detect_visual(image_path: str = None, text_prompt: str = "defect",
                      dataset: str = None) -> dict:
        """Simulate SAM3 text-prompt detection on a real Kaggle dataset.

        Returns a detection record that points at a real sample image re-hosted
        under /samples/ and carries bounding boxes in the image's native
        coordinates, so the frontend can overlay boxes on actual defect pixels.
        """
        ds = _dataset(dataset)
        W, H = ds["resolution"]
        p_any = ds.get("p_any_defect", 0.4)

        if random.random() < p_any:
            if ds["id"] == "severstal":
                num_defects = random.choices([1, 2, 3], weights=[70, 22, 8])[0]
            else:  # NEU + casting: single-defect frames
                num_defects = 1
        else:
            num_defects = 0

        # Pick the class(es) this frame exhibits. Each class entry carries its own
        # real sample image + native-resolution bbox (or a shared image for Severstal).
        chosen_classes = [_sample_class(ds) for _ in range(num_defects)]

        # Choose the background frame. Casting has distinct OK vs defective samples;
        # NEU picks the sample that matches the defect class; Severstal reuses the
        # one redistributable clean strip.
        frame = _choose_frame(ds, chosen_classes)
        native_w, native_h = frame["native_size"]

        detections = []
        for c in chosen_classes:
            # Prefer the real bbox bundled with the class; otherwise clamp the
            # area hint into the frame's native coordinate system.
            bbox = c.get("bbox")
            if bbox is None:
                area = c.get("area_px") or 128
                bw = min(max(int(area * random.uniform(0.6, 1.4)), 20),
                         max(30, native_w // 3))
                bh = min(max(int(area * random.uniform(0.6, 1.4)), 20),
                         max(30, native_h // 2))
                x = random.randint(0, max(1, native_w - bw))
                y = random.randint(0, max(1, native_h - bh))
                bbox = [x, y, bw, bh]
            detections.append({
                "type": c["type"],
                "label": c["label"],
                "severity": c["severity"],
                "area_px": c.get("area_px"),
                "bbox": bbox,
                "confidence": round(random.uniform(0.82, 0.98), 3),
                "prompt": text_prompt,
            })

        # Sample filename drawn from the dataset's naming convention (for the log line)
        if image_path is None:
            if ds["id"] == "severstal":
                image_path = f"severstal/{random.randrange(1, ds['total_images']):04x}.jpg"
            elif ds["id"] == "neu":
                cls = chosen_classes[0]["type"] if chosen_classes else random.choice(ds["classes"])["type"]
                image_path = f"neu-det/{cls}_{random.randint(1, 300)}.jpg"
            else:
                folder = "def_front" if chosen_classes else "ok_front"
                image_path = f"casting/{folder}/cast_{folder}_{random.randint(1, 3758):04d}.jpeg"

        return {
            "model": "SAM3",
            "image": image_path,
            "image_url": frame["url"],
            "native_size": [native_w, native_h],
            "resolution": [W, H],
            "text_prompt": text_prompt,
            "num_detections": len(detections),
            "detections": detections,
            "inference_ms": round(random.uniform(25, 45), 1),
            "dataset": {
                "id": ds["id"],
                "name": ds["name"],
                "source": ds["source"],
                "url": ds["url"],
                "total_images": ds["total_images"],
                "classes": [{"type": c["type"], "label": c["label"],
                             "count": c.get("count"), "prior": c.get("prior")}
                            for c in ds["classes"]],
            },
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def detect_audio(audio_path: str = None) -> dict:
        """模拟SAM-Audio声纹分析"""
        has_anomaly = random.random() < 0.4
        anomalies = []
        if has_anomaly:
            a = random.choice(PerceptionLayer.AUDIO_ANOMALIES).copy()
            a["detected_freq_hz"] = a["freq_hz"] + random.randint(-50, 50)
            a["snr_db"] = round(random.uniform(5, 25), 1)
            anomalies.append(a)

        return {
            "model": "SAM-Audio",
            "audio": audio_path or "factory_recording.wav",
            "duration_sec": round(random.uniform(3, 10), 1),
            "num_anomalies": len(anomalies),
            "anomalies": anomalies,
            "background_noise_db": round(random.uniform(65, 85), 1),
            "timestamp": datetime.now().isoformat(),
        }


# ══════════════════════════════════════════════════
# Layer 2: 预测层 (TimesFM 模拟)
# ══════════════════════════════════════════════════

class PredictionLayer:
    """模拟TimesFM时序预测"""

    @staticmethod
    def generate_time_series(name: str, length: int = 168, trend: str = "degrading") -> list:
        """生成模拟时序数据"""
        base = {"degrading": 99.7, "stable": 99.8, "improving": 99.5}[trend]
        noise_scale = 0.05
        data = []
        for i in range(length):
            if trend == "degrading":
                val = base - (i / length) * 0.5 + random.gauss(0, noise_scale)
            elif trend == "improving":
                val = base + (i / length) * 0.2 + random.gauss(0, noise_scale)
            else:
                val = base + random.gauss(0, noise_scale)
            data.append(round(val, 4))
        return data

    @staticmethod
    def forecast(history: list, horizon: int = 72, name: str = "metric") -> dict:
        """模拟TimesFM预测"""
        if not history:
            history = PredictionLayer.generate_time_series(name, 168, "degrading")

        last_val = history[-1]
        # 简单线性趋势 + 噪声
        recent_trend = (history[-1] - history[-24]) / 24 if len(history) >= 24 else 0

        point_forecast = []
        q10, q50, q90 = [], [], []
        for h in range(horizon):
            pred = last_val + recent_trend * (h + 1)
            noise = random.gauss(0, 0.03) * math.sqrt(h + 1)
            point_forecast.append(round(pred + noise, 4))
            q10.append(round(pred - 0.15 * math.sqrt(h + 1), 4))
            q50.append(round(pred, 4))
            q90.append(round(pred + 0.15 * math.sqrt(h + 1), 4))

        # 找到跨越阈值的时间点
        threshold = 99.5
        crossing_hour = None
        for i, v in enumerate(point_forecast):
            if v < threshold:
                crossing_hour = i
                break

        return {
            "model": "TimesFM-2.5-200M",
            "metric_name": name,
            "history_length": len(history),
            "horizon": horizon,
            "point_forecast": point_forecast,
            "quantiles": {"q10": q10, "q50": q50, "q90": q90},
            "trend": round(recent_trend * 24, 4),  # 日趋势
            "threshold": threshold,
            "crossing_hour": crossing_hour,
            "alert": crossing_hour is not None,
            "alert_message": f"{name}预计在{crossing_hour}小时后降至{threshold}以下" if crossing_hour else None,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def predict_equipment_rul(sensor_data: list = None) -> dict:
        """预测设备剩余使用寿命(RUL)"""
        if not sensor_data:
            sensor_data = PredictionLayer.generate_time_series("vibration", 720, "degrading")

        result = PredictionLayer.forecast(sensor_data, 168, "设备振动")
        rul_hours = result["crossing_hour"] or random.randint(100, 300)

        return {
            **result,
            "metric_name": "设备剩余寿命(RUL)",
            "rul_hours": rul_hours,
            "rul_days": round(rul_hours / 24, 1),
            "maintenance_urgency": "紧急" if rul_hours < 48 else "计划中" if rul_hours < 168 else "正常",
            "recommended_action": f"建议在{rul_hours}小时内安排维护" if rul_hours < 168 else "正常监控",
        }


# ══════════════════════════════════════════════════
# Layer 3: 关联层 (Ontology 模拟)
# ══════════════════════════════════════════════════

class OntologyLayer:
    """模拟制造业Ontology知识图谱遍历"""

    GRAPH = {
        "涂布工位#3": {
            "设备": ["刮刀#7", "涂布辊#3", "干燥炉#3"],
            "物料": ["正极浆料-批次2024Q3-087", "铝箔-批次AF-2024-156"],
            "操作员": ["张师傅(工号T0042)"],
            "上次维护": "72小时前",
            "建议维护周期": "48小时",
        },
        "刮刀#7": {
            "类型": "逗号刮刀",
            "安装时间": "72小时前",
            "建议更换周期": "48小时",
            "状态": "超期运行",
            "关联缺陷": ["划痕", "涂布不均"],
        },
        "正极浆料-批次2024Q3-087": {
            "粘度(mPa·s)": 5200,
            "规格范围": "4800-5500",
            "状态": "在规格内但偏高",
            "供应商": "XXX材料科技",
            "入库时间": "3天前",
        },
        "电机#7": {
            "类型": "伺服电机",
            "功率": "7.5kW",
            "运行时间": "12000小时",
            "上次维护": "30天前",
            "关联设备": ["涂布辊#3"],
        },
    }

    @staticmethod
    def trace_root_cause(defect_type: str, workstation: str = "涂布工位#3") -> dict:
        """从缺陷追溯到根因"""
        ws = OntologyLayer.GRAPH.get(workstation, {})
        traces = []

        # 设备关联
        for equip in ws.get("设备", []):
            equip_info = OntologyLayer.GRAPH.get(equip, {})
            if defect_type in equip_info.get("关联缺陷", []):
                traces.append({
                    "path": f"{workstation} → {equip}",
                    "finding": equip_info.get("状态", "未知"),
                    "relevance": "high",
                    "detail": equip_info,
                })

        # 物料关联
        for mat in ws.get("物料", []):
            mat_info = OntologyLayer.GRAPH.get(mat, {})
            if mat_info:
                traces.append({
                    "path": f"{workstation} → {mat}",
                    "finding": mat_info.get("状态", "未知"),
                    "relevance": "medium",
                    "detail": mat_info,
                })

        return {
            "defect_type": defect_type,
            "workstation": workstation,
            "traces": traces,
            "graph_nodes_traversed": len(traces) + 1,
            "timestamp": datetime.now().isoformat(),
        }


# ══════════════════════════════════════════════════
# Layer 4: 归因层 (LLM 推理)
# ══════════════════════════════════════════════════

class DiagnosisLayer:
    """LLM归因分析"""

    @staticmethod
    def diagnose(perception: dict, prediction: dict, ontology: dict,
                 audio: dict = None, use_llm: bool = False) -> dict:
        """综合多源数据生成归因报告"""

        # 构建上下文
        context = {
            "visual_defects": perception.get("detections", []),
            "audio_anomalies": (audio or {}).get("anomalies", []),
            "prediction_alert": prediction.get("alert_message"),
            "rul": prediction.get("rul_hours"),
            "ontology_traces": ontology.get("traces", []),
        }

        if use_llm and BIGMODEL_KEY:
            return DiagnosisLayer._llm_diagnose(context)
        else:
            return DiagnosisLayer._rule_diagnose(context)

    @staticmethod
    def _rule_diagnose(ctx: dict) -> dict:
        """基于规则的归因（离线模式）"""
        root_causes = []

        # 分析设备关联
        for trace in ctx.get("ontology_traces", []):
            if trace["relevance"] == "high":
                detail = trace.get("detail", {})
                root_causes.append({
                    "cause": f"{trace['path']}：{trace['finding']}",
                    "confidence": 0.90,
                    "evidence": [
                        f"设备状态: {trace['finding']}",
                        f"关联路径: {trace['path']}",
                    ],
                    "action": f"立即检查/更换相关设备",
                    "priority": "紧急",
                })
            elif trace["relevance"] == "medium":
                root_causes.append({
                    "cause": f"{trace['path']}：{trace['finding']}",
                    "confidence": 0.60,
                    "evidence": [f"物料状态: {trace['finding']}"],
                    "action": "检查物料批次质检报告",
                    "priority": "高",
                })

        # 分析声纹异常
        for anomaly in ctx.get("audio_anomalies", []):
            root_causes.append({
                "cause": f"声纹检测到{anomaly['label']}（{anomaly['detected_freq_hz']}Hz）",
                "confidence": anomaly.get("confidence", 0.8),
                "evidence": [f"特征频率: {anomaly['detected_freq_hz']}Hz", f"SNR: {anomaly.get('snr_db')}dB"],
                "action": f"安排{anomaly['label']}相关设备维护",
                "priority": "高",
            })

        # 分析预测告警
        if ctx.get("prediction_alert"):
            root_causes.append({
                "cause": ctx["prediction_alert"],
                "confidence": 0.75,
                "evidence": [f"TimesFM预测", f"剩余{ctx.get('rul', '?')}小时"],
                "action": "基于预测安排预防性维护",
                "priority": "计划中",
            })

        # 排序
        root_causes.sort(key=lambda x: -x["confidence"])

        return {
            "mode": "rule-based",
            "num_root_causes": len(root_causes),
            "root_causes": root_causes,
            "summary": f"发现{len(root_causes)}个潜在根因，最高置信度{root_causes[0]['confidence']*100:.0f}%" if root_causes else "未发现异常",
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def _llm_diagnose(ctx: dict) -> dict:
        """LLM归因推理"""
        try:
            import requests
            prompt = f"""你是工业AI归因分析专家。基于以下多源检测数据，生成结构化的根因分析报告。

## 视觉检测（SAM3）
缺陷: {json.dumps(ctx['visual_defects'], ensure_ascii=False)}

## 声纹分析（SAM-Audio）
异常: {json.dumps(ctx['audio_anomalies'], ensure_ascii=False)}

## 时序预测（TimesFM）
告警: {ctx.get('prediction_alert', '无')}
设备剩余寿命: {ctx.get('rul', '未知')}小时

## 知识图谱追溯（Ontology）
关联路径: {json.dumps([t['path']+': '+t['finding'] for t in ctx.get('ontology_traces',[])], ensure_ascii=False)}

请输出JSON格式的根因分析报告：
{{"root_causes": [{{"cause":"根因描述","confidence":0.0-1.0,"evidence":["证据"],"action":"建议操作","priority":"紧急/高/中"}}], "summary":"一句话总结"}}"""

            resp = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={"Authorization": f"Bearer {BIGMODEL_KEY}", "Content-Type": "application/json"},
                json={"model": "glm-4-flash", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500},
                timeout=30,
            )
            text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            import re
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                result = json.loads(m.group())
                result["mode"] = "llm"
                result["timestamp"] = datetime.now().isoformat()
                return result
        except Exception as e:
            pass

        # Fallback
        result = DiagnosisLayer._rule_diagnose(ctx)
        result["mode"] = "llm-fallback"
        return result


# ══════════════════════════════════════════════════
# 完整管线
# ══════════════════════════════════════════════════

def run_pipeline(use_llm: bool = False, verbose: bool = True,
                 dataset: str = None) -> dict:
    """运行完整的 感知→预测→归因 管线"""

    ds = _dataset(dataset)
    if verbose:
        print(f"\n{'='*60}")
        print(f"  工业AI全链路管线：感知 → 预测 → 归因")
        print(f"  数据集: {ds['name']} ({ds['total_images']:,} imgs)")
        print(f"  模式: {'LLM归因' if use_llm else '规则归因(离线)'}")
        print(f"{'='*60}\n")

    # Layer 1: 感知
    if verbose: print("  [Layer 1] 感知层...")
    visual = PerceptionLayer.detect_visual(text_prompt="defect on surface",
                                           dataset=ds["id"])
    audio = PerceptionLayer.detect_audio()
    if verbose:
        print(f"    SAM3: 检测到 {visual['num_detections']} 个缺陷 ({visual['inference_ms']}ms)")
        for d in visual["detections"]:
            print(f"      - {d['label']} (置信度{d['confidence']}, 严重度{d['severity']})")
        print(f"    SAM-Audio: {audio['num_anomalies']} 个声纹异常")
        for a in audio["anomalies"]:
            print(f"      - {a['label']} ({a['detected_freq_hz']}Hz, 置信度{a['confidence']})")

    # Layer 2: 预测
    if verbose: print("\n  [Layer 2] 预测层...")
    yield_history = PredictionLayer.generate_time_series("良率", 168, "degrading")
    yield_pred = PredictionLayer.forecast(yield_history, 72, "良率(%)")
    rul = PredictionLayer.predict_equipment_rul()
    if verbose:
        print(f"    良率预测: 趋势{yield_pred['trend']:+.4f}/天")
        if yield_pred["alert"]:
            print(f"    ⚠️ {yield_pred['alert_message']}")
        print(f"    设备RUL: {rul['rul_hours']}小时 ({rul['maintenance_urgency']})")

    # Layer 3: 关联
    if verbose: print("\n  [Layer 3] 关联层...")
    defect_type = visual["detections"][0]["label"] if visual["detections"] else "划痕"
    ontology = OntologyLayer.trace_root_cause(defect_type)
    if verbose:
        print(f"    图谱遍历: {ontology['graph_nodes_traversed']} 个节点")
        for t in ontology["traces"]:
            print(f"      [{t['relevance']}] {t['path']}: {t['finding']}")

    # Layer 4: 归因
    if verbose: print("\n  [Layer 4] 归因层...")
    diagnosis = DiagnosisLayer.diagnose(visual, rul, ontology, audio, use_llm)
    if verbose:
        print(f"    模式: {diagnosis['mode']}")
        print(f"    {diagnosis['summary']}")
        for i, rc in enumerate(diagnosis.get("root_causes", [])[:5]):
            icon = "🔴" if rc["priority"] == "紧急" else "🟡" if rc["priority"] == "高" else "🟢"
            print(f"    {icon} [{rc['confidence']*100:.0f}%] {rc['cause']}")
            print(f"       → {rc['action']}")

    # 综合报告
    report = {
        "pipeline": "industrial-ai-v1",
        "dataset": visual.get("dataset"),
        "perception": {"visual": visual, "audio": audio},
        "prediction": {"yield": yield_pred, "rul": rul},
        "ontology": ontology,
        "diagnosis": diagnosis,
        "timestamp": datetime.now().isoformat(),
    }

    if verbose:
        print(f"\n{'='*60}")
        print(f"  管线完成 | 缺陷{visual['num_detections']}个 | RUL{rul['rul_hours']}h | 根因{diagnosis['num_root_causes']}个")
        print(f"{'='*60}\n")

    return report


# ══════════════════════════════════════════════════
# 测试数据生成
# ══════════════════════════════════════════════════

def generate_test_data():
    """生成模拟测试数据集"""
    DATA_DIR.mkdir(exist_ok=True)

    # 1. 良率时序数据（7天，每小时）
    yield_data = PredictionLayer.generate_time_series("良率", 168, "degrading")
    (DATA_DIR / "yield_history_7d.json").write_text(
        json.dumps({"metric": "良率(%)", "interval": "1h", "data": yield_data}, ensure_ascii=False, indent=2))

    # 2. 设备振动时序（30天，每小时）
    vib_data = PredictionLayer.generate_time_series("振动", 720, "degrading")
    (DATA_DIR / "vibration_30d.json").write_text(
        json.dumps({"metric": "振动(mm/s)", "interval": "1h", "data": vib_data}, ensure_ascii=False, indent=2))

    # 3. 电池衰减曲线（3000循环）
    capacity = [100 - 0.005 * i - random.gauss(0, 0.1) for i in range(3000)]
    (DATA_DIR / "battery_degradation.json").write_text(
        json.dumps({"metric": "容量保持率(%)", "interval": "1cycle", "data": [round(c, 3) for c in capacity]}, ensure_ascii=False, indent=2))

    # 4. 批量检测结果（100张图）
    batch_detections = []
    for i in range(100):
        det = PerceptionLayer.detect_visual(f"frame_{i:04d}.jpg", "defect on cell")
        batch_detections.append(det)
    (DATA_DIR / "batch_detection_100.json").write_text(
        json.dumps(batch_detections, ensure_ascii=False, indent=2))

    # 5. 声纹记录（24小时，每小时）
    audio_records = []
    for h in range(24):
        rec = PerceptionLayer.detect_audio(f"audio_hour_{h:02d}.wav")
        audio_records.append(rec)
    (DATA_DIR / "audio_24h.json").write_text(
        json.dumps(audio_records, ensure_ascii=False, indent=2))

    # 6. 完整管线运行记录（10次）
    pipeline_runs = []
    for _ in range(10):
        run = run_pipeline(use_llm=False, verbose=False)
        pipeline_runs.append(run)
    (DATA_DIR / "pipeline_runs_10.json").write_text(
        json.dumps(pipeline_runs, ensure_ascii=False, indent=2))

    print(f"  ✅ 测试数据已生成到 {DATA_DIR}/")
    for f in sorted(DATA_DIR.glob("*.json")):
        size = f.stat().st_size
        print(f"    {f.name} ({size/1024:.1f}KB)")


# ══════════════════════════════════════════════════
# CLI (only runs when executed directly)
# ══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="工业AI全链路管线")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="运行完整管线")
    p_run.add_argument("--llm", action="store_true", help="启用LLM归因")
    p_run.add_argument("--output", "-o", default="", help="输出JSON文件")

    sub.add_parser("detect", help="仅运行感知层")
    sub.add_parser("predict", help="仅运行预测层")
    sub.add_parser("diagnose", help="仅运行归因层")
    sub.add_parser("generate-data", help="生成测试数据")

    p_serve = sub.add_parser("serve", help="启动API服务器")
    p_serve.add_argument("--port", type=int, default=8770)

    args = parser.parse_args()

    if args.command == "run":
        result = run_pipeline(use_llm=args.llm)
        if args.output:
            Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"  → 报告已保存到 {args.output}")

    elif args.command == "detect":
        v = PerceptionLayer.detect_visual(text_prompt="defect on battery cell")
        a = PerceptionLayer.detect_audio()
        print(json.dumps({"visual": v, "audio": a}, ensure_ascii=False, indent=2))

    elif args.command == "predict":
        y = PredictionLayer.forecast(None, 72, "良率(%)")
        r = PredictionLayer.predict_equipment_rul()
        print(json.dumps({"yield": y, "rul": r}, ensure_ascii=False, indent=2))

    elif args.command == "diagnose":
        report = run_pipeline(use_llm=bool(BIGMODEL_KEY), verbose=False)
        print(json.dumps(report["diagnosis"], ensure_ascii=False, indent=2))

    elif args.command == "generate-data":
        generate_test_data()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
