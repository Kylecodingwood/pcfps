# RF 有监督语义分类操作指南

本文说明如何用 CloudCompare 标注、离线训练 RandomForest，并在 PCFPS 中通过派生任务 `**ml_rf_semantic**` 对滤波后的 LAS 做四类语义分类（1 地面 / 2 建筑 / 3 植被 / 4 其它）。

---

## 1. 标注（CloudCompare）

1. 从大云中裁一块代表性子区（建议含地面、建筑、植被）。
2. 分次选区，将选中点的 **Classification** 设为：
  - **1** 地面
  - **2** 建筑
  - **3** 植被
  - **4** 其它
3. 未标注点保持 **0**（训练脚本会忽略）。
4. 导出为 LAS，例如 `[terra_las/cloud_house_language.las](../terra_las/cloud_house_language.las)`。

---

## 2. 安装依赖

在仓库根目录：

```bash
pip install -r python_rf_semantic/requirements.txt
```

`python_gateway` 运行派生任务时同样需要上述包（与 `python_derived` 共用 `PYTHONPATH=.`）。

---

## 3. 训练模型（离线，只需做一次或换标注后重做）

```bash
cd /path/to/pcfps
export PYTHONPATH=.
python3 -m python_rf_semantic.train_cli \
  --labeled-las terra_las/cloud_house_language.las \
  --output-dir terra_las/rf_model_house_language
```

产出：


| 文件                    | 说明                                 |
| --------------------- | ---------------------------------- |
| `model.joblib`        | RandomForest 模型（已 gitignore，需本地生成） |
| `feature_config.json` | 特征名、PMF 参数、邻域 k                    |
| `metrics.json`        | 留出集 classification report          |


---

## 4. 服务端配置

`[backend/src/main/resources/application.yml](../backend/src/main/resources/application.yml)`：

```yaml
pcfps:
  ml-rf-semantic:
    model-dir: ${PCFPS_ML_RF_MODEL_DIR:${user.dir}/../terra_las/rf_model_house_language}
```

从 `backend/` 启动时，默认指向仓库内 `terra_las/rf_model_house_language`。也可用环境变量覆盖：

```bash
export PCFPS_ML_RF_MODEL_DIR=/绝对路径/terra_las/rf_model_house_language
```

**Python 网关**与 **Java** 需能读到同一绝对路径下的 `model.joblib`。

---

## 5. 在 PCFPS 中运行

1. 对原始 LAS 完成 **滤波** 父任务（SOR/ROR）。
2. 进入 **新建分类** → 算法选 **「RF 语义（有监督）」**。
3. 模型目录留空则用服务端默认；可选填绝对路径覆盖。
4. 提交后等待子任务 **SUCCEEDED**。
5. 任务列表 → **派生双窗**：右侧为 `classification` + `semantic_campus` 四色图例。

---

## 6. 离线推断（调试）

```bash
export PYTHONPATH=.
python3 -m python_rf_semantic.infer_cli \
  --input-las /path/to/filtered.las \
  --model-dir terra_las/rf_model_house_language \
  --output-las /tmp/out_rf_classified.las
```

---

## 7. 局限

- 模型在标注子区上训练，对全幅其它区域 **泛化有限**。
- 派生推断 `**laspy.read` 整文件进内存**，超大 LAS 请先裁切或抽稀。
- 特征邻域 **k** 须与训练时 `feature_config.json` 一致（默认 24）。

---

## 8. 与 `rule_semantic_campus` 的区别


| 项目     | 校园规则 `rule_semantic_campus` | RF `ml_rf_semantic` |
| ------ | --------------------------- | ------------------- |
| 是否需要标注 | 否li                         | 是（训练集）              |
| 机制     | 手写几何阈值                      | RandomForest + 几何特征 |
| 预览调色   | `semantic_campus` 1–4       | 相同                  |


