import csv
import random

# Configuration
TOTAL_RECORDS = 350
OUTPUT_FILE = 'work_ticket_risk_data.csv'

# Risk Categories and Templates
# Structure: (Primary Type, Secondary Type, Base Level, [List of Scenarios/Templates])
# Level adjustment logic can be added (e.g., critical keywords -> higher level)

risk_scenarios = [
    {
        "primary": "监视功能风险",
        "weight": 0.30,
        "subtypes": [
            {
                "secondary": "画面/数据不刷新",
                "weight": 0.4,
                "templates": [
                    ("[SCADA] 重启前置机fep_main进程期间，未进行主备切换，导致全网数据刷新中断{duration}。", "二级"),
                    ("[SCADA] 维护工作站进行补丁更新，误杀图形刷新进程，导致部分调度员工作站画面停止刷新。", "三级"),
                    ("[EMS] 数据库死锁导致前置应用无法写入实时数据，全网遥测数据不再更新。", "二级"),
                    ("[SCADA] 厂站通讯链路割接，配置参数错误导致某{voltage}kV变电站数据无法刷新。", "三级")
                ]
            },
            {
                "secondary": "全网/部分监控中断",
                "weight": 0.3,
                "templates": [
                    ("[SCADA] 核心交换机故障导致SCADA服务器与所有前置机断连，全网监控中断。", "一级"),
                    ("[通信] 传输设备检修导致主站至某片区所有厂站通道中断，监控盲区产生。", "二级"),
                    ("[SCADA] 服务器内存溢出导致系统核心服务崩溃，所有监控画面黑屏。", "二级"),
                    ("[Web] Web发布服务器故障，导致公司管理网用户无法查看实时监视页面。", "四级")
                ]
            },
            {
                "secondary": "告警功能失效",
                "weight": 0.3,
                "templates": [
                    ("[SCADA] 告警服务进程异常退出，期间电网事故跳闸未触发语音和推窗告警。", "二级"),
                    ("[SCADA] 修改告警定义表时误删关键字段，导致开关变位告警无法正常产生。", "二级"),
                    ("[SCADA] 告警窗频繁闪烁，运维人员临时屏蔽所有告警音响，导致新发故障未被及时发现。", "三级"),
                    ("[EMS] 事项服务器磁盘空间满，新的告警记录无法写入数据库。", "三级")
                ]
            }
        ]
    },
    {
        "primary": "控制功能风险",
        "weight": 0.15,
        "subtypes": [
            {
                "secondary": "AGC/AVC调节异常",
                "weight": 0.4,
                "templates": [
                    ("[AGC] 修改全网总负荷计算公式时符号错误，导致AGC下发错误的调节指令。", "一级"),
                    ("[AVC] 电压控制策略参数配置不当，导致某区域电压频繁波动。", "二级"),
                    ("[AGC] 联调期间误将测试模式切至运行模式，导致机组出力异常大幅波动。", "一级"),
                    ("[AGC] 遥测采样数据异常跳变，未被状态估计剔除，引发AGC误调节。", "二级")
                ]
            },
            {
                "secondary": "误发遥控/遥调指令",
                "weight": 0.3,
                "templates": [
                    ("[SCADA] 遥控测试时选错对象，误对运行中的{voltage}kV线路开关进行分闸操作。", "一级"),
                    ("[SCADA] 数据库点号映射错误，导致对A站开关操作实际作用于B站。", "一级"),
                    ("[SCADA] 自动化人员在后台直接写入遥控命令字进行测试，未经过防误闭锁逻辑。", "二级")
                ]
            },
            {
                "secondary": "控制命令拒动/超时",
                "weight": 0.3,
                "templates": [
                    ("[SCADA] 通道误码率高，导致调度员下发遥控指令超时失败。", "三级"),
                    ("[SCADA] 前置机与厂站规约解析不一致，导致遥调指令无法被执行。", "三级"),
                    ("[SCADA] 遥控返校超时参数设置过短，导致成功操作被误判为失败。", "四级")
                ]
            }
        ]
    },
    {
        "primary": "数据与软件风险",
        "weight": 0.25,
        "subtypes": [
            {
                "secondary": "历史/核心数据丢失",
                "weight": 0.3,
                "templates": [
                    ("[EMS] 历史库服务器磁盘阵列扩容误格式化分区，导致近一年历史数据丢失。", "二级"),
                    ("[EMS] 归档脚本编写错误，误删除了当月运行报表数据。", "三级"),
                    ("[SCADA] 数据库同步异常，备机启用后发现缺失最近24小时的模型参数修改记录。", "三级")
                ]
            },
            {
                "secondary": "双机/双网冗余失效",
                "weight": 0.4,
                "templates": [
                    ("[网络] 核心交换机配置错误VLAN，导致主备服务器心跳中断，双机热备失效。", "三级"),
                    ("[SCADA] 备用服务器长期未重启，接管主用服务后立即崩溃，导致单机运行风险。", "二级"),
                    ("[网络] 双平面网络配置调整，造成B网平面广播风暴，系统失去网络冗余。", "三级")
                ]
            },
            {
                "secondary": "软件功能瘫痪",
                "weight": 0.3,
                "templates": [
                    ("[PAS] 状态估计高级应用升级后无法收敛，导致网络分析功能不可用。", "四级"),
                    ("[DTS] 调度员培训模拟系统启动失败，不影响实时生产系统。", "四级"),
                    ("[OMS] 电子接线图模块更新后，无法加载厂站接线图。", "四级")
                ]
            }
        ]
    },
    {
        "primary": "网络与安全风险",
        "weight": 0.15,
        "subtypes": [
            {
                "secondary": "网络安全防线突破",
                "weight": 0.5,
                "templates": [
                    ("[安防] II区防火墙策略误开放高危端口，未限制源IP，存在入侵风险。", "二级"),
                    ("[安防] 纵向加密认证装置证书过期未及时更换，导致厂站数据无法解密上传。", "三级"),
                    ("[安防] 运维笔记本未杀毒直接接入生产网，导致病毒在内网传播。", "二级")
                ]
            },
            {
                "secondary": "网络风暴/阻塞",
                "weight": 0.5,
                "templates": [
                    ("[网络] 接入层交换机环路，引发网络风暴，导致部分工作站通讯迟滞。", "三级"),
                    ("[网络] 错误连接网线导致两个不同网段短接，造成局域网IP冲突和阻塞。", "三级"),
                    ("[数据网] 路由器OSPF配置错误，导致路由震荡，数据包大量丢失。", "三级")
                ]
            }
        ]
    },
    {
        "primary": "硬件与基础设施风险",
        "weight": 0.15,
        "subtypes": [
            {
                "secondary": "硬件设备损坏",
                "weight": 0.6,
                "templates": [
                    ("[硬件] 更换调度大屏控制器电源未佩戴防静电手环，导致控制板烧毁。", "四级"),
                    ("[硬件] 服务器内存条插拔不当造成金手指损坏，服务器无法启动。", "四级"),
                    ("[硬件] 磁盘阵列硬盘故障亮红灯，更换过程中误拔出正常硬盘。", "三级")
                ]
            },
            {
                "secondary": "供电/环境异常",
                "weight": 0.4,
                "templates": [
                    ("[环境] 机房精密空调故障停机，导致室内温度升高至35度，设备有过热宕机风险。", "三级"),
                    ("[电源] UPS蓄电池组充放电测试，未确认旁路市电正常，存在全站失电风险。", "二级"),
                    ("[环境] 机房漏水检测装置误报，导致自动排水系统启动，影响机房湿度。", "四级")
                ]
            }
        ]
    }
]

# Helper variables for dynamic generation
durations = ["3分钟", "10分钟", "30分钟", "1小时", "2小时"]
voltages = ["110", "220", "500"]

def generate_record():
    # 1. Select Primary Category
    r = random.random()
    cumulative = 0
    selected_primary = None

    for item in risk_scenarios:
        cumulative += item["weight"]
        if r <= cumulative:
            selected_primary = item
            break
    if not selected_primary:
        selected_primary = risk_scenarios[-1] # Fallback

    # 2. Select Secondary Category
    r_sub = random.random()
    cumulative_sub = 0
    selected_sub = None

    for sub in selected_primary["subtypes"]:
        cumulative_sub += sub["weight"]
        if r_sub <= cumulative_sub:
            selected_sub = sub
            break
    if not selected_sub:
        selected_sub = selected_primary["subtypes"][-1]

    # 3. Select Template
    template_tuple = random.choice(selected_sub["templates"])
    raw_text_template = template_tuple[0]
    risk_level = template_tuple[1]

    # 4. Fill Template
    text = raw_text_template.format(
        duration=random.choice(durations),
        voltage=random.choice(voltages)
    )

    return [text, selected_primary["primary"], selected_sub["secondary"], risk_level]

def main():
    header = ["原始工作票文本 (摘要)", "一级风险类型", "二级风险类型", "风险等级"]
    data = []

    for _ in range(TOTAL_RECORDS):
        data.append(generate_record())

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)

    print(f"Successfully generated {TOTAL_RECORDS} records to {OUTPUT_FILE}")

    # Calculate and print actual stats for verification
    stats = {}
    for row in data:
        p_type = row[1]
        level = row[3]
        if p_type not in stats:
            stats[p_type] = 0
        stats[p_type] += 1

    print("\nActual Distribution (Count / Total):")
    for k, v in stats.items():
        print(f"{k}: {v} ({v/TOTAL_RECORDS:.1%})")

if __name__ == "__main__":
    main()
