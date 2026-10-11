# Dynamic Bench — Isaac Sim 6.1 兼容性预览版

[English](README.md) | 简体中文

本项目是 [DynamicVLA](https://github.com/hzxie/DynamicVLA) 的**非官方 Isaac Sim 6.1 兼容迁移版**，基于上游提交 `434dc7105cf6d559018d15af5fecbcdad44f036e`。保留原作者署名、引用及许可证；不代表原作者或 NVIDIA 官方发布，也不是论文成功率复现。

原作者：Haozhe Xie、Beichen Wen、Jiarui Zheng、Zhaoxi Chen、Fangzhou Hong、Haiwen Diao、Ziwei Liu；南洋理工大学 S-Lab。

## 真实运行演示

[![Franka 牛油果放置演示](assets/demo/clean610-avocado-cover.jpg)](assets/demo/clean610-avocado-demo.mp4)

[观看10秒演示视频](assets/demo/clean610-avocado-demo.mp4)

视频于2026年10月11日由本独立兼容快照运行产生：官方 DynamicVLA DOM 权重、Franka、单环境、原始流式 LAAS 与 sleep，Isaac Sim 6.1.0.0 / Isaac Lab 3.0.0rc1。不是私有实验 runner 或历史视频。

连续两次冒烟测试均完成放置，视频展示第一次完整 episode（240帧、24 fps、10秒、三相机拼接）。**2/2只说明有限运行验收，不代表基准总体成功率；视频播放速度不代表真实墙钟延迟。** 第二次 episode 的 reset、自然终止和视频解码也已检查。完整证据与限制见 [VALIDATION.md](VALIDATION.md)。

## 迁移范围与验证边界

仅适配仿真接口：四元数边界、Warp 状态物化、相机序列化、PhysX 配置、任务导入、控制器输入和启动顺序。模型、训练、数据集及推理实现保持固定上游版本不变；保留原动作队列、推理等待与 reset/ACK 行为。

- 目标为 **Franka 单环境**。已验证启动、RGB、真实模型推理、自然终止、视频完整解码和第二次 reset。
- 多环境逐环境结果统计、其他场景、Piper、数据生成及论文成功率复现未在本公开包中验收；继承的多环境参数不等于独立终止统计已正确验证。
- 作者论文参考环境为 Sim 4.5 / Lab 2.2.1，本迁移版不是该环境。英文上游文档还包含其他版本安装说明，6.1启动请使用下文或 [PORT_README.md](PORT_README.md)。
- 保留原 Franka 夹爪参数（手指速度上限0.05 m/s、摩擦0.2），未混入后续夹爪修正，不声称跨版本接触行为等价。
- Franka 资产使用5.1内容地址前缀配合6.1运行时；资产不随包分发，需自行验证可访问性。

## 安装与快速开始

仿真目标环境：Linux、Python 3.12、Isaac Sim **6.1.0.0**、Isaac Lab **3.0.0rc1**、PhysX 后端。早期API版本不保证适用于所有后续3.x版本。

请将**仿真与模型推理分为两个环境**。按 NVIDIA 安装流程安装对应版本并完成许可证接受；仿真环境补充 `shapely pyzmq h5py`。模型环境按 [上游模型说明](README.upstream.md) 安装，不要把模型依赖无差别装入仿真环境。

资源需另外取得，本包不含权重、场景或机器人网格：

- [DOM 训练集](https://huggingface.co/datasets/hzxie/DOM)
- [DOM 测试集及部分场景](https://gateway.infinitescript.com/?f=DOM-Test)
- [DOM 三维物体](https://gateway.infinitescript.com/?f=DOM-3D-Objects)
- [DOM 完整三维场景](https://gateway.infinitescript.com/?f=DOM-3D-Scenes)
- [官方 DOM 预训练权重](https://huggingface.co/hzxie/dynamic-vla-DOM)

在本目录、仿真环境中启动：

```bash
HEADLESS=1 ENABLE_CAMERAS=1 python simulations/evaluate.py --num_envs 1 \
  --scene_dir /path/to/scenes --object_dir /path/to/objects \
  --env_cfg /path/to/test-envs.txt --output_dir /path/to/results \
  -n 20 --save
```

`-n 20` 为每个测试配置运行20次，`--save` 保存视频。测试清单中的路径须能从工作目录解析，建议使用绝对路径。**此6.1目标不接受旧 `--headless` 参数，请使用 `HEADLESS=1`；相机由 AppLauncher 启用，无需旧相机CLI参数。**

另开终端，在模型环境中启动：

```bash
python scripts/inference.py -p /path/to/official-checkpoint -r euler -d -s
```

`-p` 指定模型目录，`-r euler` 使用欧拉角，`-d` 使用相对当前状态的增量动作，`-s` 启用连续推理。条件允许时分别为仿真、推理指定不同可见GPU。

通信仅用于可信本地回环网络：继承的 Python 对象反序列化协议不适用于不可信网络。

## CPU测试与其他功能

安装 NumPy 和 PyTorch 后运行：

```bash
python -B -m unittest discover -s tests -v
```

8项CPU测试通过仅提供接口边界检查，不代替GPU闭环验收。迁移细节见 [MIGRATION.md](MIGRATION.md)，发布检查见 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)。

原项目另提供仿真数据生成、轨迹重放、LeRobot v2.1 数据转换、训练和 checkpoint 测评功能。命令与参数保留在 [README.upstream.md](README.upstream.md)；**这些流程不属于本6.1公开包已验证范围**，不能直接把上游旧版本命令视作6.1兼容保证。

## 引用

沿用上游引用信息：

```bibtex
@inproceedings{xie2026dynamicvla,
  title     = {{DynamicVLA:} A Vision-Language-Action Model for Dynamic Object Manipulation},
  author    = {Xie, Haozhe and Wen, Beichen and Zheng, Jiarui and Chen, Zhaoxi and Hong, Fangzhou and Diao, Haiwen and Liu, Ziwei},
  booktitle = {NeurIPS},
  year      = {2026}
}
```

## 许可证与分发边界

保留 [NTU S-Lab License 1.0](LICENSE)，包括**非商业使用限制**，不是MIT或Apache重新授权；商业许可请联系原权利方。仿真软件、数据集及资产另有各自条款，应分别遵守。

本包不含 Git 历史、模型权重、私有实验功能或日志、机器人网格；演示媒体仅供说明本快照的有限实际运行结果。
