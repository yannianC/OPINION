import time
import random
import requests
import threading
import os
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 先定义log_print，然后再导入pyperclip
def log_print(*args, **kwargs):
    """带时间戳的打印函数"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}]", *args, **kwargs)

try:
    import pyperclip
except ImportError:
    log_print("[系统] ⚠ 未安装pyperclip，将无法获取Balance Spot地址")
    pyperclip = None


# ============================================================================
# 基础配置和工具函数
# ============================================================================


def read_computer_config():
    """
    从同级目录下的 COMPUTER.txt 文件读取电脑配置
    
    文件格式（逗号分隔）：电脑组,IP线程数,交易/仓位线程数
    示例：23,15,10
    
    如果只有一个值，则作为电脑组号，线程数使用默认值
    
    Returns:
        tuple: (电脑组号, IP线程数, 交易线程数)
    """
    # 默认值
    default_group = "0"
    default_ip_thread_count = 15
    default_trade_thread_count = 15
    
    try:
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        computer_file = os.path.join(script_dir, "COMPUTER.txt")
        
        if os.path.exists(computer_file):
            with open(computer_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # 解析配置，支持逗号分隔
                    parts = [p.strip() for p in content.split(',')]
                    
                    # 第一个值：电脑组
                    group = parts[0] if len(parts) > 0 and parts[0] else default_group
                    
                    # 第二个值：IP线程数
                    ip_thread_count = default_ip_thread_count
                    if len(parts) > 1 and parts[1]:
                        try:
                            ip_thread_count = int(parts[1])
                        except ValueError:
                            log_print(f"[系统] ⚠ IP线程数配置无效: {parts[1]}，使用默认值: {default_ip_thread_count}")
                    
                    # 第三个值：交易/仓位线程数
                    trade_thread_count = default_trade_thread_count
                    if len(parts) > 2 and parts[2]:
                        try:
                            trade_thread_count = int(parts[2])
                        except ValueError:
                            log_print(f"[系统] ⚠ 交易线程数配置无效: {parts[2]}，使用默认值: {default_trade_thread_count}")
                    
                    log_print(f"[系统] 从 COMPUTER.txt 读取配置: 电脑组={group}, IP线程数={ip_thread_count}, 交易线程数={trade_thread_count}")
                    return (group, ip_thread_count, trade_thread_count)
                else:
                    log_print(f"[系统] ⚠ COMPUTER.txt 文件为空，使用默认配置")
                    return (default_group, default_ip_thread_count, default_trade_thread_count)
        else:
            log_print(f"[系统] ⚠ 未找到 COMPUTER.txt 文件，使用默认配置")
            return (default_group, default_ip_thread_count, default_trade_thread_count)
    except Exception as e:
        log_print(f"[系统] ⚠ 读取 COMPUTER.txt 失败: {str(e)}，使用默认配置")
        return (default_group, default_ip_thread_count, default_trade_thread_count)


def read_computer_group():
    """
    从同级目录下的 COMPUTER.txt 文件读取电脑组号（兼容旧接口）
    
    Returns:
        str: 电脑组号，如果读取失败则返回 "0"
    """
    group, _, _ = read_computer_config()
    return group


def get_browser_password(browser_id):
    """
    根据浏览器ID获取对应的密码
    优先级：特定浏览器密码 > 电脑组默认密码
    
    Args:
        browser_id: 浏览器编号（int 或 str）
        
    Returns:
        str: 对应的密码
    """
    browser_id_str = str(browser_id)
    
    # 首先检查是否有特定浏览器ID的密码配置
    if browser_id_str in SPECIFIC_BROWSER_PASSWORDS:
        password = SPECIFIC_BROWSER_PASSWORDS[browser_id_str]
        log_print(f"[{browser_id}] 使用特定浏览器密码配置")
        return password
    
    # 如果没有特定配置，使用电脑组对应的默认密码
    group_password = GROUP_PASSWORDS.get(COMPUTER_GROUP)
    if group_password:
        log_print(f"[{browser_id}] 使用电脑组 {COMPUTER_GROUP} 的默认密码")
        return group_password
    
    # 如果电脑组也没有配置，使用全局默认密码
    log_print(f"[{browser_id}] ⚠ 电脑组 {COMPUTER_GROUP} 未配置密码，使用全局默认密码")
    return DEFAULT_PASSWORD


# ============================================================================
# 配置区域
# ============================================================================

# 电脑配置（从 COMPUTER.txt 文件读取）
# 格式：电脑组,IP线程数,交易线程数
COMPUTER_GROUP, IP_THREAD_COUNT, TRADE_THREAD_COUNT = read_computer_config()

# 特定浏览器ID的密码配置
# 格式：浏览器ID: 密码
# 这些浏览器将使用指定的密码，不受电脑组影响
SPECIFIC_BROWSER_PASSWORDS = {
    # 电脑组23的特定浏览器配置
    "1": "mj@w2ndJ*kX0g8!rnsf",  # 电脑组23的浏览器1,2,3,4
    "2":"mj@w2ndJ*kX0g8!rns",
    "3": "mj@w2ndJ*kX0g8!rnsf",
    "4": "mj@w2ndJ*kX0g8!rnsf",
    "9": "qwer1234",
    "10": "qwer1234",
    "6": "5cx2Wsn#0kQnj*w240L",
    "2060": "kaznb3969*m%",  # 电脑组23的浏览器2057,2058,2059,2060
    "2057": "kaznb3969*m%",
    "2058": "kaznb3969*m%",
    "2059": "kaznb3969*m%",
    "4001": "Ok123456",
    # 电脑组9的特定浏览器配置
    "941": "cx142359.",  # 电脑组9的浏览器941-1000
    "942": "cx142359.",
    "944": "cx142359.",
    "945": "cx142359.",
    "946": "cx142359.",
    "947": "cx142359.",
    "948": "cx142359.",
    "949": "cx142359.",
    "950": "cx142359.",
    "951": "cx142359.",
    "952": "cx142359.",
    "953": "cx142359.",
    "954": "cx142359.",
    "955": "cx142359.",
    "956": "cx142359.",
    "957": "cx142359.",
    "958": "cx142359.",
    "959": "cx142359.",
    "960": "cx142359.",
    "961": "cx142359.",
    "962": "cx142359.",
    "963": "cx142359.",
    "964": "cx142359.",
    "965": "cx142359.",
    "966": "cx142359.",
    "967": "cx142359.",
    "968": "cx142359.",
    "969": "cx142359.",
    "970": "cx142359.",
    "971": "cx142359.",
    "972": "cx142359.",
    "973": "cx142359.",
    "974": "cx142359.",
    "975": "cx142359.",
    "976": "cx142359.",
    "977": "cx142359.",
    "978": "cx142359.",
    "979": "cx142359.",
    "980": "cx142359.",
    "981": "cx142359.",
    "982": "cx142359.",
    "983": "cx142359.",
    "984": "cx142359.",
    "985": "cx142359.",
    "986": "cx142359.",
    "987": "cx142359.",
    "988": "cx142359.",
    "989": "cx142359.",
    "990": "cx142359.",
    "991": "cx142359.",
    "992": "cx142359.",
    "993": "cx142359.",
    "994": "cx142359.",
    "995": "cx142359.",
    "996": "cx142359.",
    "997": "cx142359.",
    "998": "cx142359.",
    "999": "cx142359.",
    "1000": "cx142359.",
    "206":"cx142359.",
    "207":"cx142359.",
    "208":"cx142359.",
    "209":"cx142359.",
    "210":"cx142359.",
    "211":"cx142359.",
    "212":"cx142359.",
    "213":"cx142359.",
    "214":"cx142359.",
    "215":"cx142359.",
    "216":"cx142359.",
    "217":"cx142359.",
    "218":"cx142359.",
    "219":"cx142359.",
    "220":"cx142359.",
    "221":"cx142359.",
    "222":"cx142359.",
    "223":"cx142359.",
    
}

# 电脑组对应的默认密码配置
# 格式：电脑组号: 密码
# 除了在 SPECIFIC_BROWSER_PASSWORDS 中指定的浏览器外，其他浏览器使用对应电脑组的密码
GROUP_PASSWORDS = {
    "0": "Ok123456",  # 电脑组0的密码
    "1": "qwer1234",  # 电脑组1的密码
    "2": "ywj000805*",  # 电脑组2的密码
    "3": "Qrfv*Fjh87gg",  # 电脑组3的密码
    "4": "@#nsgaSBF224",  # 电脑组4的密码
    "5": "Qsst-455fgdf8",  # 电脑组5的密码
    "6": "zxcvbnm123#",  # 电脑组6的密码
    "7": "cx142359.",  # 电脑组7的密码
    "8": "ywj000805*",  # 电脑组8的密码
    "9": "Qwer009qaz`",  # 电脑组9的密码（浏览器941-1000使用特定密码，其他使用此密码）
    "10": "yhCHG^&145",
    "11": "jhJ89891",  # 电脑组11的密码
    "12": "Hhgj*liu-khHy5",  # 电脑组12的密码
    "13": "shdjjeG@^68Jhg",  # 电脑组13的密码
    "14": "gkj^&HGkhh45",  # 电脑组14的密码
    "15": " kaznb3969*m%",  # 电脑组15的密码
    "16": "ggTG*h785Wunj",  # 电脑组16的密码
    "21": "kjakln3*zhjql3",  # 电脑组21的密码
    "22": "ttRo451YU*58",  # 电脑组22的密码
    "23": "mj@w2ndJ*kX0g8!rns",  # 电脑组23的密码（浏览器1,2,3,4使用特定密码）
    "24": "5cx2Wsn#0kQnj*w240",  # 电脑组24的密码
    "25": "kashg2*dk2F",  # 电脑组25的密码
    "26": "cxknwlJK&*f8",  # 电脑组26的密码
    "27": "kiIH78hjfi.*+*",  # 电脑组27的密码
    "900": "Ok123456",  # 电脑组0的密码
    "901": "qwer1234",  # 电脑组1的密码
    "902": "ywj000805*",  # 电脑组2的密码
    "903": "Qrfv*Fjh87gg",  # 电脑组3的密码
    "904": "@#nsgaSBF224",  # 电脑组4的密码
    "905": "Qsst-455fgdf8",  # 电脑组5的密码
    "906": "zxcvbnm123#",  # 电脑组6的密码
    "907": "cx142359.",  # 电脑组7的密码
    "908": "ywj000805*",  # 电脑组8的密码
    "909": "Qwer009qaz`",  # 电脑组9的密码（浏览器941-1000使用特定密码，其他使用此密码）
    "910": "yhCHG^&145",
    "911": "jhJ89891",  # 电脑组11的密码
    "912": "Hhgj*liu-khHy5",  # 电脑组12的密码
    "913": "shdjjeG@^68Jhg",  # 电脑组13的密码
    "914": "gkj^&HGkhh45",  # 电脑组14的密码
    "915": " kaznb3969*m%",  # 电脑组15的密码
    "916": "ggTG*h785Wunj",  # 电脑组16的密码
    "921": "kjakln3*zhjql3",  # 电脑组21的密码
    "922": "ttRo451YU*58",  # 电脑组22的密码
    "923": "mj@w2ndJ*kX0g8!rns",  # 电脑组23的密码（浏览器1,2,3,4使用特定密码）
    "924": "5cx2Wsn#0kQnj*w240",  # 电脑组24的密码
    "925": "kashg2*dk2F",  # 电脑组25的密码
    "926": "cxknwlJK&*f8",  # 电脑组26的密码
    "927": "kiIH78hjfi.*+*",  # 电脑组27的密码
}

# 全局默认密码（仅当电脑组未在 GROUP_PASSWORDS 中配置时使用）
DEFAULT_PASSWORD = "Ok123456"

# 服务器API配置
SERVER_BASE_URL = "https://sg.bicoin.com.cn/99l"

# AdsPower配置
ADSPOWER_BASE_URL = "http://127.0.0.1:50325"
ADSPOWER_API_KEY = "506664c47e5e174036720d305c7b9732"
FINGERPRINT_TO_USERID = {}

# 目标页面
TARGET_URL_1 = "https://app.opinion.trade/detail?topicId=212&type=multi"
TARGET_URL_2 = "https://app.opinion.trade/profile"

# 最大重试次数
MAX_RETRIES = 3

# 线程数（从 COMPUTER.txt 读取的 IP_THREAD_COUNT）
THREAD_COUNT = IP_THREAD_COUNT

# API接口
API_BASE_URL = "https://sg.bicoin.com.cn/99l"
GET_IP_INFO_URL = f"{API_BASE_URL}/bro/getAllIpInfo"
UPDATE_IP_INFO_URL = f"{API_BASE_URL}/bro/updateIpInfo"

# 浏览器ID锁字典，用于确保同一浏览器ID同时只有一个任务在执行
BROWSER_LOCKS = {}
BROWSER_LOCKS_LOCK = threading.Lock()  # 保护BROWSER_LOCKS字典的锁

# 浏览器ID队列字典，用于存储同一浏览器ID的待处理IP
BROWSER_QUEUES = {}
BROWSER_QUEUES_LOCK = threading.Lock()  # 保护BROWSER_QUEUES字典的锁

# 浏览器ID处理状态字典，用于标记某个浏览器ID是否正在处理
BROWSER_PROCESSING = {}
BROWSER_PROCESSING_LOCK = threading.Lock()  # 保护BROWSER_PROCESSING字典的锁

# 全局线程池，用于控制所有任务的并发数
GLOBAL_THREAD_POOL = None
GLOBAL_THREAD_POOL_LOCK = threading.Lock()  # 保护全局线程池的锁

def initialize_fingerprint_mapping():
    """
    初始化浏览器编号到用户ID的映射数据
    """
    global FINGERPRINT_TO_USERID
    
    # 映射数据
    mapping_data = """3100	k15mek1c
3099	k15mek1b
3098	k15mek19
3097	k15mek18
3096	k15mek17
3095	k15mek16
3094	k15mek15
3093	k15mek14
3092	k15mek13
3091	k15mek12
3090	k15mek11
3089	k15mek10
3088	k15mek0x
3087	k15mek0w
3086	k15mek0v
3085	k15mek0u
3084	k15mek0t
3083	k15mek0s
3082	k15mek0r
3081	k15mek0q
3080	k15mek0p
3079	k15mek0o
3078	k15mek0m
3077	k15mek0l
3076	k15mek0k
3075	k15mek0j
3074	k15mek0i
3073	k15mek0h
3072	k15mek0g
3071	k15mek0f
3070	k15mek0e
3069	k15mek0d
3068	k15mek0c
3067	k15mek0b
3066	k15mek0a
3065	k15mek09
3064	k15mek08
3063	k15mek07
3062	k15mek06
3061	k15mek04
3060	k15mek03
3059	k15mek02
3058	k15mek00
3057	k15mejyy
3056	k15mejyx
3055	k15mejyv
3054	k15mejyu
3053	k15mejyt
3052	k15mejys
3051	k15mejyr
3050	k15mejyq
3049	k15mejyp
3048	k15mejyo
3047	k15mejyn
3046	k15mejym
3045	k15mejyl
3044	k15mejyk
3043	k15mejyj
3042	k15mejyi
3041	k15mejyh
3040	k15mejyg
3039	k15mejyf
3038	k15mejye
3037	k15mejyd
3036	k15mejyc
3035	k15mejyb
3034	k15mejya
3033	k15mejy9
3032	k15mejy8
3031	k15mejy7
3030	k15mejy6
3029	k15mejy5
3028	k15mejy3
3027	k15mejy0
3026	k15mejxx
3025	k15mejxw
3024	k15mejxv
3023	k15mejxt
3022	k15mejxs
3021	k15mejxr
3020	k15mejxq
3019	k15mejxp
3018	k15mejxo
3017	k15mejxn
3016	k15mejxl
3015	k15mejxk
3014	k15mejxi
3013	k15mejxh
3012	k15mejxg
3011	k15mejxf
3010	k15mejxe
3009	k15mejxd
3008	k15mejxc
3007	k15mejxb
3006	k15mejxa
3005	k15mejx9
3004	k15mejx8
3003	k15mejx7
3002	k15mejx6
3001	k15mejx5
3000	k15mejx4
2999	k15mejx3
2998	k15mejx2
2997	k15mejx1
2996	k15mejx0
2995	k15mejwy
2994	k15mejwx
2993	k15mejww
2992	k15mejwv
2991	k15mejwu
2990	k15mejwt
2989	k15mejws
2988	k15mejwr
2987	k15mejwq
2986	k15mejwp
2985	k15mejwo
2984	k15mejwn
2983	k15mejwm
2982	k15mejwl
2981	k15mejwk
2980	k15mejwj
2979	k15mejwi
2978	k15mejwh
2977	k15mejwg
2976	k15mejwf
2975	k15mejwe
2974	k15mejwd
2973	k15mejwc
2972	k15mejwb
2971	k15mejwa
2970	k15mejw9
2969	k15mejw8
2968	k15mejw7
2967	k15mejw6
2966	k15mejw5
2965	k15mejw4
2964	k15mejw3
2963	k15mejw1
2962	k15mejvy
2961	k15mejvx
2960	k15mejvv
2959	k15mejvu
2958	k15mejvt
2957	k15mejvs
2956	k15mejvr
2955	k15mejvq
2954	k15mejvp
2953	k15mejvo
2952	k15mejvm
2951	k15mejvl
2950	k15mejvk
2949	k15mejvj
2948	k15mejvh
2947	k15mejvg
2946	k15mejvf
2945	k15mejve
2944	k15mejvd
2943	k15mejvb
2942	k15mejva
2941	k15mejv9
2940	k15mejv8
2939	k15mejv7
2938	k15mejv6
2937	k15mejv5
2936	k15mejv3
2935	k15mejv2
2934	k15mejv1
2933	k15mejv0
2932	k15mejuy
2931	k15mejux
2930	k15mejuw
2929	k15mejuv
2928	k15mejuu
2927	k15mejut
2926	k15mejus
2925	k15mejur
2924	k15mejuq
2923	k15mejup
2922	k15mejuo
2921	k15mejum
2920	k15mejul
2919	k15mejuk
2918	k15mejuj
2917	k15mejui
2916	k15mejuh
2915	k15mejug
2914	k15mejuf
2913	k15mejue
2912	k15mejud
2911	k15mejuc
2910	k15mejub
2909	k15mejua
2908	k15meju9
2907	k15meju6
2906	k15meju5
2905	k15meju4
2904	k15meju2
2903	k15meju0
2902	k15mejtx
2901	k15mejtv
2900	k15mejtu
2899	k15mejts
2898	k15mejtr
2897	k15mejtq
2896	k15mejtp
2895	k15mejto
2894	k15mejtn
2893	k15mejtm
2892	k15mejtl
2891	k15mejtk
2890	k15mejtj
2889	k15mejti
2888	k15mejth
2887	k15mejtf
2886	k15mejte
2885	k15mejtd
2884	k15mejtc
2883	k15mejta
2882	k15mejt9
2881	k15mejt8
2880	k15mejt7
2879	k15mejt6
2878	k15mejt5
2877	k15mejt2
2876	k15mejt0
2875	k15mejsy
2874	k15mejsx
2873	k15mejsv
2872	k15mejsu
2871	k15mejss
2870	k15mejsr
2869	k15mejsq
2868	k15mejsp
2867	k15mejso
2866	k15mejsn
2865	k15mejsl
2864	k15mejsk
2863	k15mejsj
2862	k15mejsi
2861	k15mejsh
2860	k15mejsg
2859	k15mejsf
2858	k15mejse
2857	k15mejsd
2856	k15mejsc
2855	k15mejsb
2854	k15mejsa
2853	k15mejs9
2852	k15mejs7
2851	k15mejs6
2850	k15mejs4
2849	k15mejs3
2848	k15mejs2
2847	k15mejs1
2846	k15mejs0
2845	k15mejry
2844	k15mejrx
2843	k15mejru
2842	k15mejrs
2841	k15mejrp
2840	k15mejro
2839	k15mejrn
2838	k15mejrm
2837	k15mejrl
2836	k15mejrk
2835	k15mejrj
2834	k15mejri
2833	k15mejrh
2832	k15mejrg
2831	k15mejrf
2830	k15mejre
2829	k15mejrd
2828	k15mejrb
2827	k15mejra
2826	k15mejr9
2825	k15mejr8
2824	k15mejr7
2823	k15mejr6
2822	k15mejr4
2821	k15mejr2
2820	k15mejr1
2819	k15mejr0
2818	k15mejqy
2817	k15mejqx
2816	k15mejqv
2815	k15mejqt
2814	k15mejqs
2813	k15mejqr
2812	k15mejqq
2811	k15mejqp
2810	k15mejqn
2809	k15mejqm
2808	k15mejql
2807	k15mejqk
2806	k15mejqj
2805	k15mejqi
2804	k15mejqh
2803	k15mejqg
2802	k15mejqf
2801	k15mejqd
2800	k15mejqc
2799	k15mejqb
2798	k15mejqa
2797	k15mejq9
2796	k15mejq7
2795	k15mejq6
2794	k15mejq5
2793	k15mejq4
2792	k15mejq3
2791	k15mejq2
2790	k15mejq1
2789	k15mejq0
2788	k15mejpy
2787	k15mejpx
2786	k15mejpw
2785	k15mejpv
2784	k15mejpu
2783	k15mejpt
2782	k15mejps
2781	k15mejpr
2780	k15mejpq
2779	k15mejpo
2778	k15mejpn
2777	k15mejpm
2776	k15mejpl
2775	k15mejpj
2774	k15mejph
2773	k15mejpg
2772	k15mejpf
2771	k15mejpd
2770	k15mejpc
2769	k15mejpb
2768	k15mejpa
2767	k15mejp9
2766	k15mejp8
2765	k15mejp6
2764	k15mejp5
2763	k15mejp4
2762	k15mejp3
2761	k15mejp2
2760	k15mejp1
2759	k15mejp0
2758	k15mejoy
2757	k15mejox
2756	k15mejow
2755	k15mejov
2754	k15mejou
2753	k15mejos
2752	k15mejor
2751	k15mejoq
2750	k15mejoo
2749	k15mejon
2748	k15mejom
2747	k15mejol
2746	k15mejok
2745	k15mejoj
2744	k15mejoh
2743	k15mejof
2742	k15mejoe
2741	k15mejod
2740	k15mejoc
2739	k15mejob
2738	k15mejoa
2737	k15mejo9
2736	k15mejo6
2735	k15mejo5
2734	k15mejo3
2733	k15mejo2
2732	k15mejo1
2731	k15mejny
2730	k15mejnw
2729	k15mejnv
2728	k15mejnu
2727	k15mejnt
2726	k15mejns
2725	k15mejnr
2724	k15mejno
2723	k15mejnn
2722	k15mejnm
2721	k15mejnl
2720	k15mejnk
2719	k15mejnj
2718	k15mejni
2717	k15mejnh
2716	k15mejnf
2715	k15mejne
2714	k15mejnd
2713	k15mejnb
2712	k15mejna
2711	k15mejn9
2710	k15mejn8
2709	k15mejn7
2708	k15mejn6
2707	k15mejn5
2706	k15mejn4
2705	k15mejn3
2704	k15mejn2
2703	k15mejn1
2702	k15mejn0
2701	k15mejmy
2700	k15mejmx
2699	k15mejmw
2698	k15mejmv
2697	k15mejmu
2696	k15mejmt
2695	k15mejms
2694	k15mejmr
2693	k15mejmq
2692	k15mejmp
2691	k15mejmn
2690	k15mejmm
2689	k15mejml
2688	k15mejmk
2687	k15mejmi
2686	k15mejmh
2685	k15mejmf
2684	k15mejme
2683	k15mejmd
2682	k15mejmc
2681	k15mejmb
2680	k15mejma
2679	k15mejm9
2678	k15mejm8
2677	k15mejm7
2676	k15mejm5
2675	k15mejm4
2674	k15mejm3
2673	k15mejm2
2672	k15mejm1
2671	k15mejm0
2670	k15mejly
2669	k15mejlx
2668	k15mejlw
2667	k15mejlv
2666	k15mejlu
2665	k15mejlt
2664	k15mejls
2663	k15mejlr
2662	k15mejlq
2661	k15mejlp
2660	k15mejlo
2659	k15mejln
2658	k15mejlm
2657	k15mejll
2656	k15mejlk
2655	k15mejli
2654	k15mejlh
2653	k15mejlg
2652	k15mejle
2651	k15mejld
2650	k15mejlc
2649	k15mejlb
2648	k15mejl9
2647	k15mejl7
2646	k15mejl6
2645	k15mejl5
2644	k15mejl4
2643	k15mejl3
2642	k15mejl1
2641	k15mejl0
2640	k15mejky
2639	k15mejkx
2638	k15mejkw
2637	k15mejkv
2636	k15mejku
2635	k15mejkt
2634	k15mejks
2633	k15mejkr
2632	k15mejkq
2631	k15mejkp
2630	k15mejko
2629	k15mejkn
2628	k15mejkm
2627	k15mejkl
2626	k15mejkk
2625	k15mejki
2624	k15mejkf
2623	k15mejkd
2622	k15mejka
2621	k15mejk7
2620	k15mejk5
2619	k15mejk3
2618	k15mejk1
2617	k15mejjy
2616	k15mejjw
2615	k15mejjv
2614	k15mejju
2613	k15mejjt
2612	k15mejjr
2611	k15mejjq
2610	k15mejjp
2609	k15mejjn
2608	k15mejjl
2607	k15mejjk
2606	k15mejjj
2605	k15mejjh
2604	k15mejjg
2603	k15mejjf
2602	k15mejjd
2601	k15mejjc
2600	k15ma7sx
2599	k15ma7sw
2598	k15ma7sv
2597	k15ma7su
2596	k15ma7st
2595	k15ma7ss
2594	k15ma7sq
2593	k15ma7sp
2592	k15ma7so
2591	k15ma7sn
2590	k15ma7sm
2589	k15ma7sl
2588	k15ma7sk
2587	k15ma7si
2586	k15ma7sh
2585	k15ma7sg
2584	k15ma7sf
2583	k15ma7se
2582	k15ma7sd
2581	k15ma7sc
2580	k15ma7sb
2579	k15ma7sa
2578	k15ma7s9
2577	k15ma7s8
2576	k15ma7s7
2575	k15ma7s6
2574	k15ma7s4
2573	k15ma7s3
2572	k15ma7s2
2571	k15ma7s1
2570	k15ma7ry
2569	k15ma7rx
2568	k15ma7rw
2567	k15ma7rv
2566	k15ma7ru
2565	k15ma7rt
2564	k15ma7rs
2563	k15ma7rq
2562	k15ma7rp
2561	k15ma7ro
2560	k15ma7rn
2559	k15ma7rm
2558	k15ma7rl
2557	k15ma7rk
2556	k15ma7rj
2555	k15ma7ri
2554	k15ma7rh
2553	k15ma7rg
2552	k15ma7rf
2551	k15ma7re
2550	k15ma7rd
2549	k15ma7rc
2548	k15ma7rb
2547	k15ma7ra
2546	k15ma7r9
2545	k15ma7r8
2544	k15ma7r7
2543	k15ma7r6
2542	k15ma7r5
2541	k15ma7r3
2540	k15ma7r1
2539	k15ma7r0
2538	k15ma7qy
2537	k15ma7qx
2536	k15ma7qw
2535	k15ma7qv
2534	k15ma7qu
2533	k15ma7qt
2532	k15ma7qs
2531	k15ma7qr
2530	k15ma7qq
2529	k15ma7qp
2528	k15ma7qo
2527	k15ma7qn
2526	k15ma7qm
2525	k15ma7ql
2524	k15ma7qk
2523	k15ma7qj
2522	k15ma7qi
2521	k15ma7qh
2520	k15ma7qg
2519	k15ma7qf
2518	k15ma7qe
2517	k15ma7qd
2516	k15ma7qc
2515	k15ma7qb
2514	k15ma7q9
2513	k15ma7q8
2512	k15ma7q7
2511	k15ma7q6
2510	k15ma7q5
2509	k15ma7q4
2508	k15ma7q3
2507	k15ma7q2
2506	k15ma7q1
2505	k15ma7q0
2504	k15ma7py
2503	k15ma7px
2502	k15ma7pw
2501	k15ma7pv
2500	k15ma7pu
2499	k15ma7pt
2498	k15ma7ps
2497	k15ma7pr
2496	k15ma7pq
2495	k15ma7pp
2494	k15ma7po
2493	k15ma7pn
2492	k15ma7pm
2491	k15ma7pl
2490	k15ma7pi
2489	k15ma7ph
2488	k15ma7pg
2487	k15ma7pf
2486	k15ma7pe
2485	k15ma7pd
2484	k15ma7pc
2483	k15ma7pb
2482	k15ma7pa
2481	k15ma7p9
2480	k15ma7p8
2479	k15ma7p7
2478	k15ma7p6
2477	k15ma7p5
2476	k15ma7p4
2475	k15ma7p3
2474	k15ma7p2
2473	k15ma7p1
2472	k15ma7oy
2471	k15ma7ow
2470	k15ma7ou
2469	k15ma7os
2468	k15ma7op
2467	k15ma7on
2466	k15ma7ol
2465	k15ma7oj
2464	k15ma7og
2463	k15ma7of
2462	k15ma7od
2461	k15ma7oa
2460	k15ma7o9
2459	k15ma7o8
2458	k15ma7o7
2457	k15ma7o6
2456	k15ma7o5
2455	k15ma7o4
2454	k15ma7o3
2453	k15ma7o2
2452	k15ma7o1
2451	k15ma7o0
2450	k15ma7ny
2449	k15ma7nx
2448	k15ma7nw
2447	k15ma7nu
2446	k15ma7ns
2445	k15ma7nr
2444	k15ma7nq
2443	k15ma7np
2442	k15ma7no
2441	k15ma7nn
2440	k15ma7nm
2439	k15ma7nl
2438	k15ma7nk
2437	k15ma7nj
2436	k15ma7ni
2435	k15ma7nh
2434	k15ma7ng
2433	k15ma7nf
2432	k15ma7ne
2431	k15ma7nd
2430	k15ma7nb
2429	k15ma7na
2428	k15ma7n9
2427	k15ma7n8
2426	k15ma7n7
2425	k15ma7n6
2424	k15ma7n5
2423	k15ma7n4
2422	k15ma7n3
2421	k15ma7n2
2420	k15ma7n0
2419	k15ma7my
2418	k15ma7mx
2417	k15ma7mw
2416	k15ma7mv
2415	k15ma7mu
2414	k15ma7mt
2413	k15ma7mq
2412	k15ma7mp
2411	k15ma7mo
2410	k15ma7mn
2409	k15ma7ml
2408	k15ma7mk
2407	k15ma7mj
2406	k15ma7mh
2405	k15ma7mf
2404	k15ma7me
2403	k15ma7md
2402	k15ma7mc
2401	k15ma7mb
2400	k15ma6ji
2399	k15ma6jh
2398	k15ma6jg
2397	k15ma6jf
2396	k15ma6je
2395	k15ma6jd
2394	k15ma6jc
2393	k15ma6jb
2392	k15ma6ja
2391	k15ma6j9
2390	k15ma6j8
2389	k15ma6j7
2388	k15ma6j6
2387	k15ma6j5
2386	k15ma6j4
2385	k15ma6j3
2384	k15ma6j2
2383	k15ma6j1
2382	k15ma6j0
2381	k15ma6iy
2380	k15ma6ix
2379	k15ma6iw
2378	k15ma6iv
2377	k15ma6iu
2376	k15ma6it
2375	k15ma6is
2374	k15ma6ir
2373	k15ma6iq
2372	k15ma6ip
2371	k15ma6in
2370	k15ma6im
2369	k15ma6il
2368	k15ma6ik
2367	k15ma6ij
2366	k15ma6ii
2365	k15ma6ih
2364	k15ma6ig
2363	k15ma6if
2362	k15ma6ie
2361	k15ma6id
2360	k15ma6ic
2359	k15ma6ib
2358	k15ma6i9
2357	k15ma6i8
2356	k15ma6i7
2355	k15ma6i6
2354	k15ma6i5
2353	k15ma6i4
2352	k15ma6i3
2351	k15ma6i2
2350	k15ma6i0
2349	k15ma6hy
2348	k15ma6hx
2347	k15ma6hw
2346	k15ma6hv
2345	k15ma6hu
2344	k15ma6ht
2343	k15ma6hs
2342	k15ma6hr
2341	k15ma6hq
2340	k15ma6ho
2339	k15ma6hn
2338	k15ma6hm
2337	k15ma6hl
2336	k15ma6hk
2335	k15ma6hj
2334	k15ma6hi
2333	k15ma6hh
2332	k15ma6hf
2331	k15ma6he
2330	k15ma6hd
2329	k15ma6hb
2328	k15ma6ha
2327	k15ma6h9
2326	k15ma6h8
2325	k15ma6h6
2324	k15ma6h5
2323	k15ma6h4
2322	k15ma6h3
2321	k15ma6h2
2320	k15ma6h1
2319	k15ma6h0
2318	k15ma6gy
2317	k15ma6gx
2316	k15ma6gw
2315	k15ma6gu
2314	k15ma6gt
2313	k15ma6gs
2312	k15ma6gr
2311	k15ma6gq
2310	k15ma6gp
2309	k15ma6go
2308	k15ma6gn
2307	k15ma6gm
2306	k15ma6gl
2305	k15ma6gk
2304	k15ma6gj
2303	k15ma6gi
2302	k15ma6gh
2301	k15ma6gg
2300	k15ma6gf
2299	k15ma6ge
2298	k15ma6gd
2297	k15ma6gc
2296	k15ma6ga
2295	k15ma6g9
2294	k15ma6g8
2293	k15ma6g7
2292	k15ma6g6
2291	k15ma6g5
2290	k15ma6g4
2289	k15ma6g3
2288	k15ma6g2
2287	k15ma6g0
2286	k15ma6fy
2285	k15ma6fx
2284	k15ma6fv
2283	k15ma6fu
2282	k15ma6ft
2281	k15ma6fs
2280	k15ma6fr
2279	k15ma6fq
2278	k15ma6fp
2277	k15ma6fo
2276	k15ma6fm
2275	k15ma6fl
2274	k15ma6fk
2273	k15ma6fj
2272	k15ma6fi
2271	k15ma6fh
2270	k15ma6fg
2269	k15ma6ff
2268	k15ma6fe
2267	k15ma6fd
2266	k15ma6fc
2265	k15ma6fb
2264	k15ma6fa
2263	k15ma6f9
2262	k15ma6f8
2261	k15ma6f6
2260	k15ma6f5
2259	k15ma6f4
2258	k15ma6f3
2257	k15ma6f2
2256	k15ma6f1
2255	k15ma6ey
2254	k15ma6ew
2253	k15ma6ev
2252	k15ma6eu
2251	k15ma6et
2250	k15ma6er
2249	k15ma6ep
2248	k15ma6eo
2247	k15ma6en
2246	k15ma6em
2245	k15ma6el
2244	k15ma6ek
2243	k15ma6ej
2242	k15ma6ei
2241	k15ma6eh
2240	k15ma6eg
2239	k15ma6ef
2238	k15ma6ee
2237	k15ma6ed
2236	k15ma6eb
2235	k15ma6ea
2234	k15ma6e9
2233	k15ma6e8
2232	k15ma6e7
2231	k15ma6e6
2230	k15ma6e5
2229	k15ma6e4
2228	k15ma6e3
2227	k15ma6e1
2226	k15ma6e0
2225	k15ma6dy
2224	k15ma6dx
2223	k15ma6dw
2222	k15ma6dv
2221	k15ma6du
2220	k15ma6dt
2219	k15ma6ds
2218	k15ma6dr
2217	k15ma6dq
2216	k15ma6dp
2215	k15ma6do
2214	k15ma6dn
2213	k15ma6dm
2212	k15ma6dl
2211	k15ma6dk
2210	k15ma6di
2209	k15ma6dh
2208	k15ma6dg
2207	k15ma6df
2206	k15ma6de
2205	k15ma6dd
2204	k15ma6dc
2203	k15ma6da
2202	k15ma6d9
2201	k15ma6d8
2200	k15jmeyu
2199	k15jmeys
2198	k15jmeyq
2197	k15jmeyn
2196	k15jmeyl
2195	k15jmeyj
2194	k15jmeyh
2193	k15jmeyf
2192	k15jmeyd
2191	k15jmeyb
2190	k15jmey9
2189	k15jmey7
2188	k15jmey6
2187	k15jmey5
2186	k15jmey4
2185	k15jmey3
2184	k15jmey2
2183	k15jmey1
2182	k15jmey0
2181	k15jmexy
2180	k15jmexw
2179	k15jmexv
2178	k15jmexu
2177	k15jmexs
2176	k15jmexr
2175	k15jmexq
2174	k15jmexp
2173	k15jmexo
2172	k15jmexm
2171	k15jmexl
2170	k15jmexj
2169	k15jmexh
2168	k15jmexg
2167	k15jmexf
2166	k15jmexd
2165	k15jmexb
2164	k15jmexa
2163	k15jmex9
2162	k15jmex8
2161	k15jmex7
2160	k15jmex6
2159	k15jmex4
2158	k15jmex3
2157	k15jmex1
2156	k15jmewx
2155	k15jmeww
2154	k15jmewv
2153	k15jmewu
2152	k15jmewt
2151	k15jmews
2150	k15jmewr
2149	k15jmewq
2148	k15jmewp
2147	k15jmewo
2146	k15jmewn
2145	k15jmewm
2144	k15jmewl
2143	k15jmewk
2142	k15jmewi
2141	k15jmewh
2140	k15jmewg
2139	k15jmewf
2138	k15jmewe
2137	k15jmewd
2136	k15jmewc
2135	k15jmewb
2134	k15jmewa
2133	k15jmew9
2132	k15jmew8
2131	k15jmew7
2130	k15jmew6
2129	k15jmew5
2128	k15jmew4
2127	k15jmew2
2126	k15jmew0
2125	k15jmevy
2124	k15jmevx
2123	k15jmevw
2122	k15jmevv
2121	k15jmevu
2120	k15jmevt
2119	k15jmevs
2118	k15jmevr
2117	k15jmevq
2116	k15jmevo
2115	k15jmevm
2114	k15jmevl
2113	k15jmevk
2112	k15jmevj
2111	k15jmevi
2110	k15jmevh
2109	k15jmevg
2108	k15jmevf
2107	k15jmeve
2106	k15jmevd
2105	k15jmevc
2104	k15jmevb
2103	k15jmeva
2102	k15jmev9
2101	k15jmev8
2100	k15jmev7
2099	k15jmev6
2098	k15jmev5
2097	k15jmev4
2096	k15jmev3
2095	k15jmev2
2094	k15jmev1
2093	k15jmev0
2092	k15jmeux
2091	k15jmeuw
2090	k15jmeuv
2089	k15jmeuu
2088	k15jmeut
2087	k15jmeus
2086	k15jmeuq
2085	k15jmeup
2084	k15jmeuo
2083	k15jmeun
2082	k15jmeum
2081	k15jmeul
2080	k15jmeuj
2079	k15jmeui
2078	k15jmeug
2077	k15jmeuf
2076	k15jmeue
2075	k15jmeud
2074	k15jmeub
2073	k15jmeu9
2072	k15jmeu8
2071	k15jmeu7
2070	k15jmeu6
2069	k15jmeu5
2068	k15jmeu3
2067	k15jmeu2
2066	k15jmeu1
2065	k15jmeu0
2064	k15jmety
2063	k15jmetx
2062	k15jmetw
2061	k15jmetu
2060	k15jmett
2059	k15jmets
2058	k15jmetq
2057	k15jmetp
2056	k15jmeto
2055	k15jmetn
2054	k15jmetm
2053	k15jmetl
2052	k15jmetk
2051	k15jmetj
2050	k15jmeti
2049	k15jmeth
2048	k15jmetg
2047	k15jmetf
2046	k15jmete
2045	k15jmetc
2044	k15jmeta
2043	k15jmet7
2042	k15jmet4
2041	k15jmet1
2040	k15jmesx
2039	k15jmesu
2038	k15jmess
2037	k15jmesp
2036	k15jmesm
2035	k15jmesk
2034	k15jmesh
2033	k15jmesd
2032	k15jmesa
2031	k15jmes6
2030	k15jmes3
2029	k15jmery
2028	k15jmeru
2027	k15jmerr
2026	k15jmero
2025	k15jmerl
2024	k15jmeri
2023	k15jmerg
2022	k15jmerd
2021	k15jmera
2020	k15jmer8
2019	k15jmer7
2018	k15jmer6
2017	k15jmer5
2016	k15jmer4
2015	k15jmer3
2014	k15jmer2
2013	k15jmer1
2012	k15jmer0
2011	k15jmeqy
2010	k15jmeqx
2009	k15jmeqw
2008	k15jmeqv
2007	k15jmequ
2006	k15jmeqt
2005	k15jmeqr
2004	k15jmeqq
2003	k15jmeqp
2002	k15jmeqo
2001	k15jmeqn
2000	k15jmeql
1999	k15jmeqk
1998	k15jmeqj
1997	k15jmeqi
1996	k15jmeqh
1995	k15jmeqg
1994	k15jmeqe
1993	k15jmeqd
1992	k15jmeqc
1991	k15jmeqb
1990	k15jmeqa
1989	k15jmeq9
1988	k15jmeq8
1987	k15jmeq7
1986	k15jmeq6
1985	k15jmeq4
1984	k15jmeq3
1983	k15jmeq2
1982	k15jmeq1
1981	k15jmeq0
1980	k15jmepy
1979	k15jmepx
1978	k15jmepw
1977	k15jmepu
1976	k15jmept
1975	k15jmeps
1974	k15jmepr
1973	k15jmepq
1972	k15jmepo
1971	k15jmepn
1970	k15jmepm
1969	k15jmepl
1968	k15jmepk
1967	k15jmepj
1966	k15jmepi
1965	k15jmeph
1964	k15jmepg
1963	k15jmepf
1962	k15jmepe
1961	k15jmepd
1960	k15jmepc
1959	k15jmepb
1958	k15jmep9
1957	k15jmep8
1956	k15jmep7
1955	k15jmep6
1954	k15jmep5
1953	k15jmep3
1952	k15jmep2
1951	k15jmep1
1950	k15jmep0
1949	k15jmeoy
1948	k15jmeox
1947	k15jmeow
1946	k15jmeov
1945	k15jmeou
1944	k15jmeot
1943	k15jmeos
1942	k15jmeoq
1941	k15jmeop
1940	k15jmeoo
1939	k15jmeom
1938	k15jmeol
1937	k15jmeok
1936	k15jmeoj
1935	k15jmeoi
1934	k15jmeoh
1933	k15jmeog
1932	k15jmeof
1931	k15jmeoe
1930	k15jmeod
1929	k15jmeob
1928	k15jmeo8
1927	k15jmeo7
1926	k15jmeo6
1925	k15jmeo5
1924	k15jmeo4
1923	k15jmeo3
1922	k15jmeo2
1921	k15jmeo1
1920	k15jmeo0
1919	k15jmeny
1918	k15jmenx
1917	k15jmenv
1916	k15jment
1915	k15jmens
1914	k15jmenr
1913	k15jmenq
1912	k15jmenp
1911	k15jmeno
1910	k15jmenn
1909	k15jmenm
1908	k15jmenk
1907	k15jmenj
1906	k15jmeni
1905	k15jmenh
1904	k15jmeng
1903	k15jmenf
1902	k15jmene
1901	k15jmend
1900	k15jmenc
1899	k15jmenb
1898	k15jmena
1897	k15jmen9
1896	k15jmen8
1895	k15jmen7
1894	k15jmen5
1893	k15jmen4
1892	k15jmen3
1891	k15jmen1
1890	k15jmen0
1889	k15jmemy
1888	k15jmemx
1887	k15jmemw
1886	k15jmemv
1885	k15jmemu
1884	k15jmemt
1883	k15jmems
1882	k15jmemr
1881	k15jmemp
1880	k15jmemo
1879	k15jmemn
1878	k15jmemm
1877	k15jmeml
1876	k15jmemk
1875	k15jmemj
1874	k15jmemh
1873	k15jmemg
1872	k15jmemf
1871	k15jmeme
1870	k15jmemd
1869	k15jmemc
1868	k15jmemb
1867	k15jmema
1866	k15jmem9
1865	k15jmem8
1864	k15jmem7
1863	k15jmem5
1862	k15jmem4
1861	k15jmem3
1860	k15jmem2
1859	k15jmem1
1858	k15jmem0
1857	k15jmely
1856	k15jmelx
1855	k15jmelw
1854	k15jmelu
1853	k15jmelt
1852	k15jmels
1851	k15jmelr
1850	k15jmelq
1849	k15jmelp
1848	k15jmelo
1847	k15jmeln
1846	k15jmelm
1845	k15jmell
1844	k15jmelk
1843	k15jmelj
1842	k15jmeli
1841	k15jmelh
1840	k15jmelg
1839	k15jmelf
1838	k15jmele
1837	k15jmeld
1836	k15jmelc
1835	k15jmelb
1834	k15jmel9
1833	k15jmel8
1832	k15jmel7
1831	k15jmel6
1830	k15jmel5
1829	k15jmel4
1828	k15jmel3
1827	k15jmel2
1826	k15jmel1
1825	k15jmel0
1824	k15jmeky
1823	k15jmekx
1822	k15jmekw
1821	k15jmeku
1820	k15jmekt
1819	k15jmeks
1818	k15jmekr
1817	k15jmekq
1816	k15jmekp
1815	k15jmeko
1814	k15jmekn
1813	k15jmekm
1812	k15jmekl
1811	k15jmekj
1810	k15jmeki
1809	k15jmekh
1808	k15jmekg
1807	k15jmekf
1806	k15jmeke
1805	k15jmekd
1804	k15jmekc
1803	k15jmekb
1802	k15jmeka
1801	k15jmek8
1800	k15jmek7
1799	k15jmek6
1798	k15jmek5
1797	k15jmek4
1796	k15jmek2
1795	k15jmek1
1794	k15jmek0
1793	k15jmejx
1792	k15jmejw
1791	k15jmejv
1790	k15jmeju
1789	k15jmejt
1788	k15jmejs
1787	k15jmejq
1786	k15jmejp
1785	k15jmejo
1784	k15jmejn
1783	k15jmejm
1782	k15jmejl
1781	k15jmejk
1780	k15jmejj
1779	k15jmeji
1778	k15jmejh
1777	k15jmejg
1776	k15jmejf
1775	k15jmeje
1774	k15jmejd
1773	k15jmeja
1772	k15jmej9
1771	k15jmej8
1770	k15jmej7
1769	k15jmej6
1768	k15jmej5
1767	k15jmej4
1766	k15jmej3
1765	k15jmej2
1764	k15jmej1
1763	k15jmej0
1762	k15jmeix
1761	k15jmeiv
1760	k15jmeiu
1759	k15jmeit
1758	k15jmeis
1757	k15jmeir
1756	k15jmeiq
1755	k15jmeip
1754	k15jmeio
1753	k15jmein
1752	k15jmeim
1751	k15jmeil
1750	k15jmeik
1749	k15jmeij
1748	k15jmeii
1747	k15jmeig
1746	k15jmeie
1745	k15jmeid
1744	k15jmeic
1743	k15jmeib
1742	k15jmeia
1741	k15jmei9
1740	k15jmei8
1739	k15jmei7
1738	k15jmei6
1737	k15jmei5
1736	k15jmei4
1735	k15jmei3
1734	k15jmei2
1733	k15jmei1
1732	k15jmei0
1731	k15jmehy
1730	k15jmehx
1729	k15jmehw
1728	k15jmehv
1727	k15jmehu
1726	k15jmeht
1725	k15jmehs
1724	k15jmehr
1723	k15jmehq
1722	k15jmehp
1721	k15jmeho
1720	k15jmehn
1719	k15jmehm
1718	k15jmehl
1717	k15jmehk
1716	k15jmehj
1715	k15jmehh
1714	k15jmehg
1713	k15jmehe
1712	k15jmehd
1711	k15jmehc
1710	k15jmehb
1709	k15jmeha
1708	k15jmeh8
1707	k15jmeh7
1706	k15jmeh6
1705	k15jmeh5
1704	k15jmeh4
1703	k15jmeh3
1702	k15jmeh2
1701	k15jmeh1
1700	k15jmegy
1699	k15jmegx
1698	k15jmegw
1697	k15jmegv
1696	k15jmegu
1695	k15jmegt
1694	k15jmegs
1693	k15jmegr
1692	k15jmegq
1691	k15jmegp
1690	k15jmego
1689	k15jmegn
1688	k15jmegm
1687	k15jmegl
1686	k15jmegk
1685	k15jmegj
1684	k15jmegi
1683	k15jmegh
1682	k15jmegg
1681	k15jmegf
1680	k15jmege
1679	k15jmegc
1678	k15jmegb
1677	k15jmega
1676	k15jmeg9
1675	k15jmeg8
1674	k15jmeg7
1673	k15jmeg6
1672	k15jmeg5
1671	k15jmeg4
1670	k15jmeg3
1669	k15jmeg2
1668	k15jmeg1
1667	k15jmeg0
1666	k15jmefy
1665	k15jmefx
1664	k15jmefw
1663	k15jmefv
1662	k15jmefu
1661	k15jmeft
1660	k15jmefs
1659	k15jmefr
1658	k15jmefq
1657	k15jmefp
1656	k15jmefo
1655	k15jmefn
1654	k15jmefm
1653	k15jmefl
1652	k15jmefk
1651	k15jmefj
1650	k15jmefi
1649	k15jmefh
1648	k15jmefg
1647	k15jmeff
1646	k15jmefe
1645	k15jmefd
1644	k15jmefc
1643	k15jmefb
1642	k15jmef9
1641	k15jmef8
1640	k15jmef7
1639	k15jmef6
1638	k15jmef5
1637	k15jmef4
1636	k15jmef3
1635	k15jmef2
1634	k15jmef1
1633	k15jmef0
1632	k15jmeey
1631	k15jmeex
1630	k15jmeew
1629	k15jmeev
1628	k15jmeeu
1627	k15jmeet
1626	k15jmees
1625	k15jmeer
1624	k15jmeep
1623	k15jmeeo
1622	k15jmeen
1621	k15jmeem
1620	k15jmeel
1619	k15jmeek
1618	k15jmeej
1617	k15jmeeh
1616	k15jmeeg
1615	k15jmeef
1614	k15jmeee
1613	k15jmeed
1612	k15jmeeb
1611	k15jmeea
1610	k15jmee9
1609	k15jmee8
1608	k15jmee7
1607	k15jmee5
1606	k15jmee2
1605	k15jmee1
1604	k15jmee0
1603	k15jmedy
1602	k15jmedx
1601	k15jmedv
1600	k15jmedu
1599	k15jmedr
1598	k15jmedp
1597	k15jmedn
1596	k15jmedl
1595	k15jmedj
1594	k15jmedh
1593	k15jmedf
1592	k15jmedd
1591	k15jmedb
1590	k15jmed9
1589	k15jmed7
1588	k15jmed6
1587	k15jmed5
1586	k15jmed4
1585	k15jmed3
1584	k15jmed2
1583	k15jmed1
1582	k15jmed0
1581	k15jmecy
1580	k15jmecx
1579	k15jmecw
1578	k15jmecu
1577	k15jmect
1576	k15jmecs
1575	k15jmecr
1574	k15jmecq
1573	k15jmecp
1572	k15jmeco
1571	k15jmecn
1570	k15jmecm
1569	k15jmeck
1568	k15jmecj
1567	k15jmeci
1566	k15jmech
1565	k15jmecg
1564	k15jmecf
1563	k15jmece
1562	k15jmecd
1561	k15jmecb
1560	k15jmeca
1559	k15jmec9
1558	k15jmec8
1557	k15jmec7
1556	k15jmec6
1555	k15jmec5
1554	k15jmec4
1553	k15jmec3
1552	k15jmec2
1551	k15jmec1
1550	k15jmec0
1549	k15jmebx
1548	k15jmebw
1547	k15jmebu
1546	k15jmebt
1545	k15jmebs
1544	k15jmebr
1543	k15jmebq
1542	k15jmebo
1541	k15jmebk
1540	k15jmebi
1539	k15jmebf
1538	k15jmebd
1537	k15jmeba
1536	k15jmeb8
1535	k15jmeb6
1534	k15jmeb4
1533	k15jmeb3
1532	k15jmeb1
1531	k15jmeb0
1530	k15jmeax
1529	k15jmeav
1528	k15jmeau
1527	k15jmeat
1526	k15jmeas
1525	k15jmear
1524	k15jmeaq
1523	k15jmeap
1522	k15jmeao
1521	k15jmean
1520	k15jmeam
1519	k15jmeak
1518	k15jmeaj
1517	k15jmeai
1516	k15jmeah
1515	k15jmeag
1514	k15jmeaf
1513	k15jmeae
1512	k15jmead
1511	k15jmeac
1510	k15jmeab
1509	k15jmeaa
1508	k15jmea9
1507	k15jmea8
1506	k15jmea6
1505	k15jmea4
1504	k15jmea2
1503	k15jmea1
1502	k15jme9x
1501	k15jme9w
1500	k15jme9t
1499	k15jme9s
1498	k15jme9p
1497	k15jme9n
1496	k15jme9m
1495	k15jme9k
1494	k15jme9j
1493	k15jme9i
1492	k15jme9h
1491	k15jme9g
1490	k15jme9f
1489	k15jme9e
1488	k15jme9c
1487	k15jme9b
1486	k15jme9a
1485	k15jme99
1484	k15jme98
1483	k15jme97
1482	k15jme96
1481	k15jme95
1480	k15jme94
1479	k15jme93
1478	k15jme92
1477	k15jme91
1476	k15jme90
1475	k15jme8y
1474	k15jme8x
1473	k15jme8v
1472	k15jme8u
1471	k15jme8t
1470	k15jme8s
1469	k15jme8q
1468	k15jme8p
1467	k15jme8o
1466	k15jme8n
1465	k15jme8m
1464	k15jme8l
1463	k15jme8k
1462	k15jme8j
1461	k15jme8i
1460	k15jme8h
1459	k15jme8g
1458	k15jme8f
1457	k15jme8e
1456	k15jme8d
1455	k15jme8c
1454	k15jme8b
1453	k15jme88
1452	k15jme87
1451	k15jme86
1450	k15jme85
1449	k15jme84
1448	k15jme83
1447	k15jme82
1446	k15jme81
1445	k15jme7y
1444	k15jme7w
1443	k15jme7v
1442	k15jme7u
1441	k15jme7t
1440	k15jme7s
1439	k15jme7r
1438	k15jme7q
1437	k15jme7p
1436	k15jme7n
1435	k15jme7m
1434	k15jme7k
1433	k15jme7j
1432	k15jme7i
1431	k15jme7g
1430	k15jme7f
1429	k15jme7e
1428	k15jme7d
1427	k15jme7b
1426	k15jme7a
1425	k15jme79
1424	k15jme78
1423	k15jme77
1422	k15jme76
1421	k15jme75
1420	k15jme74
1419	k15jme72
1418	k15jme71
1417	k15jme70
1416	k15jme6y
1415	k15jme6x
1414	k15jme6w
1413	k15jme6v
1412	k15jme6u
1411	k15jme6t
1410	k15jme6s
1409	k15jme6q
1408	k15jme6o
1407	k15jme6m
1406	k15jme6k
1405	k15jme6i
1404	k15jme6g
1403	k15jme6e
1402	k15jme6c
1401	k15jme6a
1400	k15jme68
1399	k15jme67
1398	k15jme65
1397	k15jme64
1396	k15jme63
1395	k15jme62
1394	k15jme60
1393	k15jme5y
1392	k15jme5x
1391	k15jme5w
1390	k15jme5v
1389	k15jme5u
1388	k15jme5t
1387	k15jme5s
1386	k15jme5r
1385	k15jme5p
1384	k15jme5o
1383	k15jme5n
1382	k15jme5m
1381	k15jme5l
1380	k15jme5k
1379	k15jme5j
1378	k15jme5i
1377	k15jme5h
1376	k15jme5g
1375	k15jme5f
1374	k15jme5e
1373	k15jme5d
1372	k15jme5c
1371	k15jme5b
1370	k15jme5a
1369	k15jme59
1368	k15jme58
1367	k15jme57
1366	k15jme56
1365	k15jme55
1364	k15jme53
1363	k15jme52
1362	k15jme51
1361	k15jme50
1360	k15jme4y
1359	k15jme4x
1358	k15jme4w
1357	k15jme4u
1356	k15jme4s
1355	k15jme4q
1354	k15jme4o
1353	k15jme4m
1352	k15jme4j
1351	k15jme4h
1350	k15jme4e
1349	k15jme4b
1348	k15jme49
1347	k15jme47
1346	k15jme46
1345	k15jme45
1344	k15jme44
1343	k15jme43
1342	k15jme42
1341	k15jme41
1340	k15jme40
1339	k15jme3y
1338	k15jme3x
1337	k15jme3w
1336	k15jme3v
1335	k15jme3u
1334	k15jme3s
1333	k15jme3r
1332	k15jme3q
1331	k15jme3p
1330	k15jme3o
1329	k15jme3m
1328	k15jme3k
1327	k15jme3j
1326	k15jme3h
1325	k15jme3f
1324	k15jme3e
1323	k15jme3d
1322	k15jme3c
1321	k15jme3b
1320	k15jme3a
1319	k15jme38
1318	k15jme37
1317	k15jme36
1316	k15jme35
1315	k15jme34
1314	k15jme33
1313	k15jme32
1312	k15jme31
1311	k15jme30
1310	k15jme2y
1309	k15jme2w
1308	k15jme2v
1307	k15jme2u
1306	k15jme2t
1305	k15jme2s
1304	k15jme2r
1303	k15jme2p
1302	k15jme2o
1301	k15jme2n
1300	k15jme2m
1299	k15jme2l
1298	k15jme2k
1297	k15jme2j
1296	k15jme2i
1295	k15jme2h
1294	k15jme2g
1293	k15jme2f
1292	k15jme2e
1291	k15jme2d
1290	k15jme2c
1289	k15jme2b
1288	k15jme2a
1287	k15jme28
1286	k15jme27
1285	k15jme25
1284	k15jme24
1283	k15jme23
1282	k15jme22
1281	k15jme20
1280	k15jme1y
1279	k15jme1x
1278	k15jme1v
1277	k15jme1u
1276	k15jme1s
1275	k15jme1r
1274	k15jme1p
1273	k15jme1n
1272	k15jme1m
1271	k15jme1l
1270	k15jme1k
1269	k15jme1j
1268	k15jme1h
1267	k15jme1g
1266	k15jme1f
1265	k15jme1d
1264	k15jme1c
1263	k15jme1a
1262	k15jme19
1261	k15jme18
1260	k15jme17
1259	k15jme16
1258	k15jme14
1257	k15jme13
1256	k15jme12
1255	k15jme11
1254	k15jme10
1253	k15jme0y
1252	k15jme0x
1251	k15jme0w
1250	k15jme0v
1249	k15jme0u
1248	k15jme0t
1247	k15jme0s
1246	k15jme0r
1245	k15jme0p
1244	k15jme0o
1243	k15jme0n
1242	k15jme0m
1241	k15jme0l
1240	k15jme0k
1239	k15jme0i
1238	k15jme0h
1237	k15jme0g
1236	k15jme0f
1235	k15jme0e
1234	k15jme0d
1233	k15jme0c
1232	k15jme0b
1231	k15jme0a
1230	k15jme09
1229	k15jme08
1228	k15jme07
1227	k15jme06
1226	k15jme05
1225	k15jme03
1224	k15jme02
1223	k15jme01
1222	k15jme00
1221	k15jmdyy
1220	k15jmdyw
1219	k15jmdyv
1218	k15jmdyu
1217	k15jmdyt
1216	k15jmdys
1215	k15jmdyq
1214	k15jmdyp
1213	k15jmdyo
1212	k15jmdyn
1211	k15jmdym
1210	k15jmdyl
1209	k15jmdyk
1208	k15jmdyj
1207	k15jmdyh
1206	k15jmdyg
1205	k15jmdyf
1204	k15jmdye
1203	k15jmdyd
1202	k15jmdyc
1201	k15jmdya
1200	k15iai33
1199	k15iai32
1198	k15iai31
1197	k15iai30
1196	k15iai2y
1195	k15iai2x
1194	k15iai2v
1193	k15iai2u
1192	k15iai2t
1191	k15iai2s
1190	k15iai2r
1189	k15iai2q
1188	k15iai2p
1187	k15iai2o
1186	k15iai2n
1185	k15iai2m
1184	k15iai2l
1183	k15iai2k
1182	k15iai2j
1181	k15iai2i
1180	k15iai2h
1179	k15iai2g
1178	k15iai2f
1177	k15iai2d
1176	k15iai2b
1175	k15iai2a
1174	k15iai29
1173	k15iai28
1172	k15iai27
1171	k15iai26
1170	k15iai25
1169	k15iai24
1168	k15iai23
1167	k15iai22
1166	k15iai21
1165	k15iai20
1164	k15iai1y
1163	k15iai1x
1162	k15iai1w
1161	k15iai1u
1160	k15iai1t
1159	k15iai1s
1158	k15iai1r
1157	k15iai1q
1156	k15iai1p
1155	k15iai1o
1154	k15iai1n
1153	k15iai1m
1152	k15iai1l
1151	k15iai1k
1150	k15iai1j
1149	k15iai1i
1148	k15iai1h
1147	k15iai1e
1146	k15iai1d
1145	k15iai1c
1144	k15iai1b
1143	k15iai1a
1142	k15iai19
1141	k15iai18
1140	k15iai17
1139	k15iai16
1138	k15iai15
1137	k15iai14
1136	k15iai13
1135	k15iai12
1134	k15iai11
1133	k15iai10
1132	k15iai0y
1131	k15iai0x
1130	k15iai0w
1129	k15iai0v
1128	k15iai0t
1127	k15iai0s
1126	k15iai0q
1125	k15iai0p
1124	k15iai0n
1123	k15iai0m
1122	k15iai0l
1121	k15iai0k
1120	k15iai0j
1119	k15iai0i
1118	k15iai0h
1117	k15iai0g
1116	k15iai0f
1115	k15iai0e
1114	k15iai0d
1113	k15iai0c
1112	k15iai0b
1111	k15iai09
1110	k15iai07
1109	k15iai05
1108	k15iai03
1107	k15iai02
1106	k15iai01
1105	k15iai00
1104	k15iahyy
1103	k15iahyw
1102	k15iahyv
1101	k15iahyu
1100	k15iahyt
1099	k15iahys
1098	k15iahyr
1097	k15iahyq
1096	k15iahyp
1095	k15iahyo
1094	k15iahyn
1093	k15iahym
1092	k15iahyl
1091	k15iahyk
1090	k15iahyj
1089	k15iahyi
1088	k15iahyf
1087	k15iahye
1086	k15iahyd
1085	k15iahyb
1084	k15iahya
1083	k15iahy9
1082	k15iahy8
1081	k15iahy7
1080	k15iahy6
1079	k15iahy5
1078	k15iahy4
1077	k15iahy3
1076	k15iahy2
1075	k15iahxy
1074	k15iahxx
1073	k15iahxw
1072	k15iahxv
1071	k15iahxu
1070	k15iahxt
1069	k15iahxs
1068	k15iahxr
1067	k15iahxp
1066	k15iahxo
1065	k15iahxn
1064	k15iahxl
1063	k15iahxk
1062	k15iahxj
1061	k15iahxi
1060	k15iahxg
1059	k15iahxf
1058	k15iahxe
1057	k15iahxd
1056	k15iahxc
1055	k15iahxb
1054	k15iahx9
1053	k15iahx8
1052	k15iahx6
1051	k15iahx5
1050	k15iahx4
1049	k15iahx3
1048	k15iahx2
1047	k15iahx1
1046	k15iahx0
1045	k15iahwy
1044	k15iahww
1043	k15iahwv
1042	k15iahwu
1041	k15iahwt
1040	k15iahws
1039	k15iahwr
1038	k15iahwp
1037	k15iahwo
1036	k15iahwm
1035	k15iahwl
1034	k15iahwk
1033	k15iahwj
1032	k15iahwi
1031	k15iahwh
1030	k15iahwf
1029	k15iahwe
1028	k15iahwc
1027	k15iahwb
1026	k15iahwa
1025	k15iahw9
1024	k15iahw7
1023	k15iahw5
1022	k15iahw4
1021	k15iahw3
1020	k15iahw2
1019	k15iahw1
1018	k15iahw0
1017	k15iahvy
1016	k15iahvx
1015	k15iahvv
1014	k15iahvu
1013	k15iahvt
1012	k15iahvs
1011	k15iahvq
1010	k15iahvp
1009	k15iahvo
1008	k15iahvn
1007	k15iahvm
1006	k15iahvk
1005	k15iahvj
1004	k15iahvi
1003	k15iahvh
1002	k15iahvg
1001	k15iahvf
1000	k15iahve
999	k15iahvd
998	k15iahvc
997	k15iahvb
996	k15iahva
995	k15iahv8
994	k15iahv7
993	k15iahv5
992	k15iahv4
991	k15iahv3
990	k15iahv2
989	k15iahv1
988	k15iahv0
987	k15iahuy
986	k15iahux
985	k15iahuw
984	k15iahuu
983	k15iahut
982	k15iahur
981	k15iahup
980	k15iahuo
979	k15iahun
978	k15iahum
977	k15iahul
976	k15iahuk
975	k15iahuj
974	k15iahui
973	k15iahug
972	k15iahuf
971	k15iahue
970	k15iahud
969	k15iahuc
968	k15iahub
967	k15iahua
966	k15iahu8
965	k15iahu7
964	k15iahu6
963	k15iahu5
962	k15iahu4
961	k15iahu3
960	k15iahu2
959	k15iahu1
958	k15iahu0
957	k15iahty
956	k15iahtx
955	k15iahtw
954	k15iahtv
953	k15iahtu
952	k15iahts
951	k15iahtr
950	k15iahtq
949	k15iahtp
948	k15iahto
947	k15iahtn
946	k15iahtm
945	k15iahtl
944	k15iahtk
943	k15iahtj
942	k15iahti
941	k15iahth
940	k15iahtg
939	k15iahtf
938	k15iahte
937	k15iahtd
936	k15iahtc
935	k15iahta
934	k15iaht9
933	k15iaht8
932	k15iaht7
931	k15iaht5
930	k15iaht3
929	k15iaht2
928	k15iaht1
927	k15iaht0
926	k15iahsx
925	k15iahsw
924	k15iahsv
923	k15iahsu
922	k15iahst
921	k15iahss
920	k15iahsr
919	k15iahsq
918	k15iahsp
917	k15iahso
916	k15iahsm
915	k15iahsl
914	k15iahsk
913	k15iahsj
912	k15iahsg
911	k15iahsf
910	k15iahse
909	k15iahsd
908	k15iahsc
907	k15iahsb
906	k15iahsa
905	k15iahs9
904	k15iahs8
903	k15iahs7
902	k15iahs6
901	k15iahs5
900	k15iahs4
899	k15iahs3
898	k15iahs1
897	k15iahs0
896	k15iahry
895	k15iahrx
894	k15iahrv
893	k15iahru
892	k15iahrt
891	k15iahrs
890	k15iahrr
889	k15iahrq
888	k15iahrp
887	k15iahrn
886	k15iahrm
885	k15iahrl
884	k15iahri
883	k15iahrh
882	k15iahrg
881	k15iahrf
880	k15iahrd
879	k15iahrb
878	k15iahra
877	k15iahr9
876	k15iahr8
875	k15iahr7
874	k15iahr6
873	k15iahr4
872	k15iahr3
871	k15iahr2
870	k15iahr1
869	k15iahr0
868	k15iahqy
867	k15iahqx
866	k15iahqw
865	k15iahqv
864	k15iahqt
863	k15iahqs
862	k15iahqr
861	k15iahqq
860	k15iahqp
859	k15iahqo
858	k15iahqn
857	k15iahql
856	k15iahqk
855	k15iahqj
854	k15iahqi
853	k15iahqh
852	k15iahqg
851	k15iahqf
850	k15iahqe
849	k15iahqd
848	k15iahqc
847	k15iahqb
846	k15iahqa
845	k15iahq8
844	k15iahq7
843	k15iahq6
842	k15iahq5
841	k15iahq4
840	k15iahq3
839	k15iahq1
838	k15iahpy
837	k15iahpx
836	k15iahpv
835	k15iahpu
834	k15iahpt
833	k15iahps
832	k15iahpr
831	k15iahpq
830	k15iahpp
829	k15iahpo
828	k15iahpn
827	k15iahpm
826	k15iahpl
825	k15iahpk
824	k15iahpj
823	k15iahpi
822	k15iahph
821	k15iahpf
820	k15iahpe
819	k15iahpd
818	k15iahpc
817	k15iahpb
816	k15iahpa
815	k15iahp8
814	k15iahp7
813	k15iahp6
812	k15iahp5
811	k15iahp4
810	k15iahp3
809	k15iahp2
808	k15iahp1
807	k15iahoy
806	k15iahox
805	k15iahow
804	k15iahov
803	k15iahou
802	k15iahot
801	k15iahor
800	k15iahoq
799	k15iahop
798	k15iahoo
797	k15iahon
796	k15iahom
795	k15iahol
794	k15iahok
793	k15iahoj
792	k15iahoi
791	k15iahoh
790	k15iahog
789	k15iahof
788	k15iahoe
787	k15iahoc
786	k15iahob
785	k15iahoa
784	k15iaho9
783	k15iaho7
782	k15iaho6
781	k15iaho5
780	k15iaho4
779	k15iaho3
778	k15iaho2
777	k15iaho1
776	k15iahny
775	k15iahnx
774	k15iahnw
773	k15iahnv
772	k15iahns
771	k15iahnr
770	k15iahnq
769	k15iahnp
768	k15iahno
767	k15iahnn
766	k15iahnm
765	k15iahnl
764	k15iahnk
763	k15iahnj
762	k15iahni
761	k15iahnh
760	k15iahng
759	k15iahne
758	k15iahnd
757	k15iahnc
756	k15iahnb
755	k15iahn9
754	k15iahn8
753	k15iahn7
752	k15iahn6
751	k15iahn5
750	k15iahn3
749	k15iahn1
748	k15iahn0
747	k15iahmy
746	k15iahmx
745	k15iahmw
744	k15iahmv
743	k15iahmt
742	k15iahms
741	k15iahmr
740	k15iahmq
739	k15iahmp
738	k15iahmo
737	k15iahmn
736	k15iahmll
735	k15iahmj
734	k15iahmg
733	k15iahme
732	k15iahmc
731	k15iahma
730	k15iahm8
729	k15iahm6
728	k15iahm4
727	k15iahm3
726	k15iahm1
725	k15iahly
724	k15iahlx
723	k15iahlw
722	k15iahlv
721	k15iahlu
720	k15iahlt
719	k15iahls
718	k15iahlr
717	k15iahlp
716	k15iahlo
715	k15iahln
714	k15iahlm
713	k15iahll
712	k15iahlk
711	k15iahlj
710	k15iahlh
709	k15iahlg
708	k15iahlf
707	k15iahle
706	k15iahld
705	k15iahlc
704	k15iahla
703	k15iahl9
702	k15iahl8
701	k15iahl7
700	k15iahl6
699	k15iahl4
698	k15iahl3
697	k15iahl2
696	k15iahl0
695	k15iahky
694	k15iahkx
693	k15iahkw
692	k15iahkv
691	k15iahku
690	k15iahkt
689	k15iahks
688	k15iahkr
687	k15iahkq
686	k15iahko
685	k15iahkn
684	k15iahkm
683	k15iahkk
682	k15iahki
681	k15iahkf
680	k15iahke
679	k15iahkd
678	k15iahkc
677	k15iahkb
676	k15iahka
675	k15iahk9
674	k15iahk8
673	k15iahk7
672	k15iahk6
671	k15iahk5
670	k15iahk4
669	k15iahk3
668	k15iahk1
667	k15iahk0
666	k15iahjy
665	k15iahjx
664	k15iahjw
663	k15iahjv
662	k15iahju
661	k15iahjt
660	k15iahjs
659	k15iahjq
658	k15iahjo
657	k15iahjn
656	k15iahjm
655	k15iahjl
654	k15iahjk
653	k15iahjj
652	k15iahji
651	k15iahjh
650	k15iahje
649	k15iahjc
648	k15iahjb
647	k15iahj9
646	k15iahj8
645	k15iahj7
644	k15iahj6
643	k15iahj5
642	k15iahj4
641	k15iahj3
640	k15iahj1
639	k15iahj0
638	k15iahiy
637	k15iahix
636	k15iahiw
635	k15iahiv
634	k15iahiu
633	k15iahit
632	k15iahis
631	k15iahiq
630	k15iahio
629	k15iahin
628	k15iahim
627	k15iahil
626	k15iahik
625	k15iahij
624	k15iahii
623	k15iahih
622	k15iahif
621	k15iahie
620	k15iahid
619	k15iahic
618	k15iahib
617	k15iahia
616	k15iahi9
615	k15iahi8
614	k15iahi7
613	k15iahi6
612	k15iahi4
611	k15iahi3
610	k15iahi2
609	k15iahi1
608	k15iahi0
607	k15iahhy
606	k15iahhx
605	k15iahhv
604	k15iahht
603	k15iahhs
602	k15iahhr
601	k15iahhq
600	k15i41cm
599	k15i3x2w
598	k15i3x2v
597	k15i3x2u
596	k15i3x2t
595	k15i3x2s
594	k15i3x2q
593	k15i3x2p
592	k15i3x2o
591	k15i3x2n
590	k15i3x2m
589	k15i3x2l
588	k15i3x2k
587	k15i3x2j
586	k15i3x2i
585	k15i3x2h
584	k15i3x2g
583	k15i3x2f
582	k15i3x2e
581	k15i3x2d
580	k15i3x2c
579	k15i3x2b
578	k15i3x2a
577	k15i3x29
576	k15i3x28
575	k15i3x27
574	k15i3x25
573	k15i3x24
572	k15i3x23
571	k15i3x22
570	k15i3x20
569	k15i3x1y
568	k15i3x1x
567	k15i3x1w
566	k15i3x1v
565	k15i3x1u
564	k15i3x1s
563	k15i3x1r
562	k15i3x1q
561	k15i3x1o
560	k15i3x1m
559	k15i3x1l
558	k15i3x1k
557	k15i3x1i
556	k15i3x1h
555	k15i3x1g
554	k15i3x1f
553	k15i3x1e
552	k15i3x1d
551	k15i3x1c
550	k15i3x1b
549	k15i3x1a
548	k15i3x19
547	k15i3x18
546	k15i3x16
545	k15i3x15
544	k15i3x14
543	k15i3x13
542	k15i3x12
541	k15i3x11
540	k15i3x10
539	k15i3x0y
538	k15i3x0x
537	k15i3x0w
536	k15i3x0v
535	k15i3x0u
534	k15i3x0t
533	k15i3x0s
532	k15i3x0r
531	k15i3x0p
530	k15i3x0o
529	k15i3x0m
528	k15i3x0k
527	k15i3x0j
526	k15i3x0i
525	k15i3x0h
524	k15i3x0g
523	k15i3x0f
522	k15i3x0e
521	k15i3x0b
520	k15i3x0a
519	k15i3x09
518	k15i3x08
517	k15i3x07
516	k15i3x06
515	k15i3x05
514	k15i3x04
513	k15i3x03
512	k15i3x02
511	k15i3x01
510	k15i3x00
509	k15i3wyy
508	k15i3wyx
507	k15i3wyw
506	k15i3wyv
505	k15i3wyu
504	k15i3wys
503	k15i3wyr
502	k15i3wyq
501	k15i3wyp
500	k15i3wyo
499	k15i3wyn
498	k15i3wym
497	k15i3wyl
496	k15i3wyk
495	k15i3wyj
494	k15i3wyi
493	k15i3wyh
492	k15i3wyg
491	k15i3wyf
490	k15i3wye
489	k15i3wyd
488	k15i3wyc
487	k15i3wyb
486	k15i3wya
485	k15i3wy8
484	k15i3wy7
483	k15i3wy6
482	k15i3wy4
481	k15i3wy3
480	k15i3wy2
479	k15i3wy1
478	k15i3wy0
477	k15i3wxy
476	k15i3wxx
475	k15i3wxw
474	k15i3wxu
473	k15i3wxt
472	k15i3wxr
471	k15i3wxq
470	k15i3wxp
469	k15i3wxo
468	k15i3wxn
467	k15i3wxm
466	k15i3wxl
465	k15i3wxk
464	k15i3wxj
463	k15i3wxi
462	k15i3wxg
461	k15i3wxf
460	k15i3wxe
459	k15i3wxd
458	k15i3wxc
457	k15i3wxb
456	k15i3wxa
455	k15i3wx9
454	k15i3wx8
453	k15i3wx7
452	k15i3wx6
451	k15i3wx5
450	k15i3wx4
449	k15i3wx2
448	k15i3wx1
447	k15i3wx0
446	k15i3wwy
445	k15i3wwx
444	k15i3www
443	k15i3wwv
442	k15i3wwu
441	k15i3wwt
440	k15i3wws
439	k15i3wwq
438	k15i3wwp
437	k15i3wwo
436	k15i3wwn
435	k15i3wwm
434	k15i3wwl
433	k15i3wwk
432	k15i3wwj
431	k15i3wwi
430	k15i3wwh
429	k15i3wwg
428	k15i3wwe
427	k15i3wwc
426	k15i3wwb
425	k15i3wwa
424	k15i3ww8
423	k15i3ww7
422	k15i3ww6
421	k15i3ww5
420	k15i3ww4
419	k15i3ww3
418	k15i3ww2
417	k15i3ww1
416	k15i3ww0
415	k15i3wvy
414	k15i3wvx
413	k15i3wvw
412	k15i3wvv
411	k15i3wvu
410	k15i3wvt
409	k15i3wvs
408	k15i3wvr
407	k15i3wvq
406	k15i3wvp
405	k15i3wvo
404	k15i3wvn
403	k15i3wvm
402	k15i3wvl
401	k15i3wvk
400	k15i3wvj
399	k15harx4
398	k15harx3
397	k15harx2
396	k15harx1
395	k15harx0
394	k15harwy
393	k15harwx
392	k15harww
391	k15harwv
390	k15harwu
389	k15harws
388	k15harwr
387	k15harwq
386	k15harwo
385	k15harwn
384	k15harwl
383	k15harwk
382	k15harwi
381	k15harwh
380	k15harwg
379	k15harwf
378	k15harwe
377	k15harwd
376	k15harwc
375	k15harwb
374	k15harwa
373	k15harw8
372	k15harw6
371	k15harw5
370	k15harw3
369	k15harw2
368	k15harw1
367	k15harw0
366	k15harvy
365	k15harvx
364	k15harvw
363	k15harvv
362	k15harvu
361	k15harvt
360	k15harvr
359	k15harvq
358	k15harvp
357	k15harvo
356	k15harvn
355	k15harvm
354	k15harvj
353	k15harvi
352	k15harvf
351	k15harve
350	k15harvc
349	k15harvb
348	k15harva
347	k15harv9
346	k15harv7
345	k15harv6
344	k15harv5
343	k15harv4
342	k15harv3
341	k15harv2
340	k15harv0
339	k15haruy
338	k15harux
337	k15haruw
336	k15haruv
335	k15haruu
334	k15harus
333	k15harur
332	k15haruq
331	k15harup
330	k15haruo
329	k15harun
328	k15harul
327	k15haruk
326	k15haruj
325	k15haruh
324	k15harug
323	k15haruf
322	k15harue
321	k15harud
320	k15harub
319	k15harua
318	k15haru9
317	k15haru8
316	k15haru6
315	k15haru5
314	k15haru4
313	k15haru3
312	k15haru2
311	k15haru1
310	k15haru0
309	k15harty
308	k15hartx
307	k15hartv
306	k15hartt
305	k15hartr
304	k15hartp
303	k15hartn
302	k15hartl
301	k15hartj
300	k15hartg
299	k15hartf
298	k15hartd
297	k15hartb
296	k15harta
295	k15hart8
294	k15hart5
293	k15hart4
292	k15hart3
291	k15hart2
290	k15dua2i
289	k15dua2g
288	k15dua2e
287	k15dua2b
286	k15dua28
285	k15dua26
284	k15dua24
283	k15dua23
282	k15dua22
281	k15dua21
280	k15dua20
279	k15dua1x
278	k15dua1w
277	k15dua1v
276	k15dua1u
275	k15dua1t
274	k15dua1s
273	k15dua1r
272	k15dua1q
271	k15dua1p
270	k15dua1o
269	k15dua1m
268	k15dua1l
267	k15dua1k
266	k15dua1j
265	k15dua1i
264	k15dua1h
263	k15dua1g
262	k15dua1f
261	k15dua1e
260	k15dua1d
259	k15dua1c
258	k15dua1b
257	k15dua1a
256	k15dua19
255	k15dua18
254	k15dua17
253	k15dua16
252	k15dua14
251	k15dua13
250	k15dua12
249	k15dua11
248	k15dua10
247	k15dua0y
246	k15dua0x
245	k15dua0w
244	k15dua0v
243	k15dua0u
242	k15dua0s
241	k15dua0r
240	k15dua0o
239	k15dua0n
238	k15dua0m
237	k15dua0l
236	k15dua0k
235	k15dua0j
234	k15dua0i
233	k15dua0h
232	k15dua0g
231	k15dua0f
230	k15dua0e
229	k15dua0d
228	k15dua0c
227	k15dua0b
226	k15dua0a
225	k15dua08
224	k15dua07
223	k15dua06
222	k15dua05
221	k15dua02
220	k15dua00
219	k15du9yx
218	k15du9yv
217	k15du9ys
216	k15du9yp
215	k15du9yn
214	k15du9yl
213	k15du9yj
212	k15du9yg
211	k15du9ye
210	k15du9yc
209	k15du9yb
208	k15du9y9
207	k15du9y8
206	k15du9y7
205	k15du9y5
204	k15du9y3
203	k15du9y2
202	k15du9y0
201	k15du9xy
200	k15du9xx
199	k15du9xw
198	k15du9xv
197	k15du9xu
196	k15du9xt
195	k15du9xs
194	k15du9xr
193	k15du9xq
192	k15du9xp
191	k15du9xo
190	k15du9xn
189	k15du9xk
188	k15du9xj
187	k15du9xi
186	k15du9xh
185	k15du9xf
184	k15du9xe
183	k15du9xd
182	k15du9xc
181	k15du9xb
180	k15du9xa
179	k15du9x9
178	k15du9x8
177	k15du9x7
176	k15du9x6
175	k15du9x4
174	k15du9x3
173	k15du9x1
172	k15du9x0
171	k15du9wy
170	k15du9wx
169	k15du9wv
168	k15du9wt
167	k15du9ws
166	k15du9wr
165	k15du9wp
164	k15du9wn
163	k15du9wm
162	k15du9wl
161	k15du9wk
160	k15du9wj
159	k15du9wi
158	k15du9wh
157	k15du9wg
156	k15du9wf
155	k15du9we
154	k15du9wd
153	k15du9wc
152	k15du9wa
151	k15du9w9
150	k15du9w7
149	k15du9w4
148	k15du9w3
147	k15du9w2
146	k15du9w0
145	k15du9vy
144	k15du9vx
143	k15du9vv
142	k15du9vt
141	k15du9vs
140	k15du9vq
139	k15du9vp
138	k15du9vn
137	k15du9vm
136	k15du9vl
135	k15du9vk
134	k15du9vi
133	k15du9vh
132	k15du9vg
131	k15du9vf
130	k15du9ve
129	k15du9vd
128	k15du9vc
127	k15du9vb
126	k15du9va
125	k15du9v9
124	k15du9v8
123	k15du9v7
122	k15du9v6
121	k15du9v5
120	k15du9v3
119	k15du9v2
118	k15du9uy
117	k15du9ux
116	k15du9uv
115	k15du9uu
114	k15du9ut
113	k15du9us
112	k15du9ur
111	k15du9uq
110	k15du9up
109	k15du9uo
108	k15du9un
107	k15du9ul
106	k15du9uj
105	k15du9ui
104	k15du9uh
103	k15du9uf
102	k15du9ue
101	k15du9ud
100	k15du9uc
99	k15du9ub
98	k15du9ua
97	k15du9u9
96	k15du9u8
95	k15du9u7
94	k15du9u6
93	k15du9u5
92	k15du9u4
91	k15du9u3
90	k15du9u2
89	k15du9u1
88	k15du9u0
87	k15du9ty
86	k15du9tx
85	k15du9tv
84	k15du9tu
83	k15du9tt
82	k15du9ts
81	k15du9tr
80	k15du9tq
79	k15du9to
78	k15du9tn
77	k15du9tm
76	k15du9tl
75	k15du9tk
74	k15du9tj
73	k15du9ti
72	k15du9tg
71	k15du9tf
70	k15du9te
69	k15du9tc
68	k15du9tb
67	k15du9ta
66	k15du9t9
65	k15du9t8
64	k15du9t6
63	k15du9t5
62	k15du9t4
61	k15du9t3
60	k15du9t2
59	k15du9t1
58	k15du9t0
57	k15du9sy
56	k15du9sx
55	k15du9sw
54	k15du9sv
53	k15du9su
52	k15du9st
51	k15du9ss
50	k15du9sr
49	k15du9sq
48	k15du9sp
47	k15du9so
46	k15du9sn
45	k15du9sm
44	k15du9sl
43	k15du9sk
42	k15du9sj
41	k15du9si
40	k15du9sh
39	k15du9sg
38	k15du9sf
37	k15du9se
36	k15du9sd
35	k15du9sc
34	k15du9sb
33	k15du9s9
32	k15du9s8
31	k15du9s7
30	k15du9s6
29	k15du9s5
28	k15du9s4
27	k15du9s3
26	k15du9s2
25	k15du9s1
24	k15du9s0
23	k15du9ry
22	k15du9rx
21	k15du9rv
20	k15du9ru
19	k15du9rs
18	k15du9rr
17	k15du9rq
16	k15du9rp
15	k15du9ro
14	k15du9rn
13	k15du9rm
12	k15du9rl
11	k15du9rk
10	k15du9rj
9	k15du9ri
8	k15du9rf
7	k15du9re
6	k15du9rd
5	k15du9rc
4	k15du9rb
3	k15du9ra
2	k15du9r9
1	k15du9r7"""
    
    # 解析映射数据
    lines = mapping_data.strip().split('\n')
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) == 2:
            browser_num = parts[0].strip()
            user_id = parts[1].strip()
            FINGERPRINT_TO_USERID[browser_num] = user_id
    
    # 添加测试浏览器映射（4001用于测试）
    FINGERPRINT_TO_USERID["4001"] = "k17cah7w"
    
    log_print(f"[系统] ✓ 已加载 {len(FINGERPRINT_TO_USERID)} 个浏览器映射")


# ============================================================================
# 任务获取和结果提交
# ============================================================================

def get_mission_from_server():
    """
    从服务器获取任务（带typelist=[11]参数）
    
    Returns:
        dict: 任务数据，如果没有任务或失败则返回None
    """
    try:
        url = f"{SERVER_BASE_URL}/mission/getOneMission"
        payload = {
            "groupNo": COMPUTER_GROUP,
            "typeList": [11]
        }
        
        log_print(f"\n[系统] 请求任务: {url}")
        log_print(f"[系统] 请求参数: {payload}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[系统] 服务器响应: {result}")
            
            if result and isinstance(result, dict):
                code = result.get("code")
                msg = result.get("msg")
                data = result.get("data")
                
                if code == 0 and data:
                    mission = data.get("mission", {})
                    
                    if mission and mission.get("id"):
                        log_print(f"[系统] ✓ 获取到任务 ID: {mission.get('id')}, 类型: {mission.get('type')}")
                        return mission
                    else:
                        log_print(f"[系统] ℹ 任务数据为空或缺少ID")
                else:
                    log_print(f"[系统] ℹ 暂无任务 (code: {code}, msg: {msg})")
            else:
                log_print(f"[系统] ℹ 服务器返回数据格式错误")
        else:
            log_print(f"[系统] ✗ 请求失败，状态码: {response.status_code}")
        
        return None
        
    except requests.exceptions.Timeout:
        log_print(f"[系统] ✗ 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        log_print(f"[系统] ✗ 连接错误")
        return None
    except Exception as e:
        log_print(f"[系统] ✗ 获取任务异常: {str(e)}")
        import traceback
        log_print(f"[系统] 异常详情:\n{traceback.format_exc()}")
        return None


def submit_mission_result(mission_id, success_count, failed_count, failed_info, status=2, custom_msg=None):
    """
    提交任务结果到服务器（带重试机制）
    
    Args:
        mission_id: 任务ID
        success_count: 成功数量
        failed_count: 失败数量
        failed_info: 失败的浏览器信息字典 {browser_id: failure_reason}
        status: 任务状态，2=成功，3=失败
        custom_msg: 自定义消息（如果提供，将使用此消息而不是默认格式）
        
    Returns:
        bool: 提交成功返回True，失败返回False
    """
    url = f"{SERVER_BASE_URL}/mission/saveResult"
    
    # 构建消息
    if custom_msg:
        # 如果提供了自定义消息，直接使用
        msg = custom_msg
    else:
        # 否则使用默认格式
        msg = f"成功: {success_count}个, 失败: {failed_count}个"
        if failed_info:
            msg += f", 失败的浏览器: {', '.join(failed_info.keys())}"
            reasons = []
            for bid, reason in failed_info.items():
                if reason:
                    reasons.append(f"{bid}{reason}")
            if reasons:
                msg += f"，其中{'，'.join(reasons)}"
    
    payload = {
        "id": mission_id,
        "status": status,  # 2=成功，3=失败
        "msg": msg
    }
    
    log_print(f"\n[系统] 提交结果: {url}")
    log_print(f"[系统] 提交数据: {payload}")
    
    # 重试机制：最多重试3次
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log_print(f"[系统] 第 {attempt + 1} 次尝试提交...")
                time.sleep(2)
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                log_print(f"[系统] 服务器响应: {result}")
                
                if result == {}:
                    log_print(f"[系统] ✓ 结果提交成功（服务器返回空字典）")
                    return True
                
                if result and isinstance(result, dict):
                    code = result.get("code")
                    server_msg = result.get("msg")
                    
                    if code == 0:
                        log_print(f"[系统] ✓ 结果提交成功")
                        return True
                    else:
                        log_print(f"[系统] ✗ 结果提交失败 (code: {code}, msg: {server_msg})")
                        if attempt < max_retries - 1:
                            continue
                        return False
                else:
                    log_print(f"[系统] ✗ 服务器返回数据格式错误")
                    if attempt < max_retries - 1:
                        continue
                    return False
            else:
                log_print(f"[系统] ✗ 结果提交失败，状态码: {response.status_code}")
                if attempt < max_retries - 1:
                    continue
                return False
                
        except requests.exceptions.Timeout:
            log_print(f"[系统] ✗ 提交超时")
            if attempt < max_retries - 1:
                continue
            return False
        except requests.exceptions.ConnectionError:
            log_print(f"[系统] ✗ 连接错误")
            if attempt < max_retries - 1:
                continue
            return False
        except Exception as e:
            log_print(f"[系统] ✗ 提交异常: {str(e)}")
            if attempt < max_retries - 1:
                continue
            import traceback
            log_print(f"[系统] 异常详情:\n{traceback.format_exc()}")
            return False
    
    return False


# ============================================================================
# 获取IP列表
# ============================================================================

def get_all_ip_info():
    """
    获取所有IP信息（带重试机制，最多3次）
    
    Returns:
        tuple: (ip_list, success) - IP信息列表和是否成功，失败返回([], False)
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log_print(f"[系统] 第 {attempt + 1} 次尝试获取IP列表...")
                time.sleep(2)
            
            group_no = read_computer_group()
            url = GET_IP_INFO_URL
            params = {"groupNo": group_no}
            
            log_print(f"[系统] 请求IP列表: {url}, 参数: {params}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    ip_list = result.get("data", {}).get("list", [])
                    log_print(f"[系统] ✓ 成功获取 {len(ip_list)} 个IP信息")
                    return ip_list, True
                else:
                    log_print(f"[系统] ✗ 获取IP列表失败: {result.get('msg')}")
                    if attempt < max_retries - 1:
                        continue
                    return [], False
            else:
                log_print(f"[系统] ✗ 获取IP列表失败: HTTP状态码 {response.status_code}")
                if attempt < max_retries - 1:
                    continue
                return [], False
        except requests.exceptions.Timeout:
            log_print(f"[系统] ✗ 获取IP列表超时")
            if attempt < max_retries - 1:
                continue
            return [], False
        except requests.exceptions.ConnectionError:
            log_print(f"[系统] ✗ 连接错误")
            if attempt < max_retries - 1:
                continue
            return [], False
        except Exception as e:
            log_print(f"[系统] ✗ 获取IP列表异常: {str(e)}")
            if attempt < max_retries - 1:
                continue
            import traceback
            log_print(f"[系统] 异常详情:\n{traceback.format_exc()}")
            return [], False
    
    return [], False


# ============================================================================
# 更新IP信息
# ============================================================================

def update_ip_info(ip_data):
    """
    更新IP信息到服务器
    
    Args:
        ip_data: IP信息字典，包含所有字段
        
    Returns:
        bool: 成功返回True
    """
    try:
        url = UPDATE_IP_INFO_URL
        # 调试：打印要上传的数据
        log_print(f"[{ip_data.get('ip', 'unknown')}] 上传IP信息: {url}")
        log_print(f"[{ip_data.get('ip', 'unknown')}] [调试] 上传数据字段: a={ip_data.get('a')}, b={ip_data.get('b')}, c={ip_data.get('c')}, d={ip_data.get('d')}, h={ip_data.get('h')}, e={ip_data.get('e')}, f={ip_data.get('f')}, g={ip_data.get('g')}, i={ip_data.get('i')}")
        response = requests.post(url, json=ip_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                log_print(f"[{ip_data.get('ip', 'unknown')}] ✓ 上传IP信息成功")
                return True
            else:
                log_print(f"[{ip_data.get('ip', 'unknown')}] ✗ 上传IP信息失败: {result.get('msg')}")
                return False
        else:
            log_print(f"[{ip_data.get('ip', 'unknown')}] ✗ 上传IP信息失败: HTTP状态码 {response.status_code}")
            return False
    except Exception as e:
        log_print(f"[{ip_data.get('ip', 'unknown')}] ✗ 上传IP信息异常: {str(e)}")
        return False


# ============================================================================
# AdsPower相关函数
# ============================================================================

def update_adspower_proxy(browser_id, proxy_config):
    """
    更新AdsPower浏览器的代理设置
    
    Args:
        browser_id: 浏览器编号
        proxy_config: 代理配置字典，包含 ip, port, username, password, type, isMain
        
    Returns:
        bool: 更新成功返回True，失败返回False
    """
    try:
        # 获取浏览器对应的用户ID
        user_id = FINGERPRINT_TO_USERID.get(str(browser_id))
        if not user_id:
            log_print(f"[{browser_id}] ✗ 无法找到浏览器对应的用户ID映射")
            return False
        
        is_main = proxy_config.get('isMain', 0)
        log_print(f"[{browser_id}] 开始更新AdsPower代理设置，用户ID: {user_id}, isMain: {is_main}")
        log_print(f"[{browser_id}] 代理信息: IP={proxy_config['ip']}, Port={proxy_config['port']}, Type={proxy_config['type']}, Username={proxy_config['username']}")
        
        # 构建更新请求
        url = f"{ADSPOWER_BASE_URL}/api/v1/user/update"
        payload = {
            "user_id": user_id,
            "user_proxy_config": {
                "proxy_host": proxy_config['ip'],
                "proxy_port": proxy_config['port'],
                "proxy_user": proxy_config['username'],
                "proxy_password": proxy_config['password'],
                "proxy_type": proxy_config['type'],
                "proxy_soft": "other"
            }
        }
        headers = {
            'Authorization': f'Bearer {ADSPOWER_API_KEY}'
        }
        
        log_print(f"[{browser_id}] 发送更新请求: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            log_print(f"[{browser_id}] 更新响应: {result}")
            code = result.get("code")
            
            if code == 0:
                log_print(f"[{browser_id}] ✓ AdsPower代理设置更新成功")
                return True
            else:
                log_print(f"[{browser_id}] ✗ AdsPower代理设置更新失败: code={code}, msg={result.get('msg')}")
                return False
        else:
            log_print(f"[{browser_id}] ✗ AdsPower代理设置更新失败: HTTP状态码 {response.status_code}")
            log_print(f"[{browser_id}] 响应内容: {response.text}")
            return False
            
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 更新AdsPower代理设置异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 异常详情:\n{traceback.format_exc()}")
        return False


def start_adspower_browser(serial_number):
    """
    启动AdsPower浏览器
    
    Args:
        serial_number: 浏览器序列号
        
    Returns:
        dict: 浏览器启动后的数据字典，失败返回None
    """
    import json
    
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/start"
    params = {
        "serial_number": serial_number,
        "user_id": "",
        "open_tabs": 1
    }
    launch_args = [f"--window-size={1500},{1700}"]
    params["launch_args"] = json.dumps(launch_args)
    headers = {
        'Authorization': f'Bearer {ADSPOWER_API_KEY}'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            log_print(f"[{serial_number}] 尝试启动浏览器 (第 {attempt + 1}/{MAX_RETRIES} 次)")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            data = response.json()
            
            if data.get("code") == 0:
                log_print(f"[{serial_number}] ✓ 浏览器启动成功")
                return data.get("data")
            else:
                log_print(f"[{serial_number}] ✗ 浏览器启动失败: {data.get('msg')}")
                
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 浏览器启动时发生异常: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(30 + 30 * attempt)
    
    log_print(f"[{serial_number}] ✗✗✗ 浏览器启动失败，已达到最大重试次数")
    return None


def close_adspower_browser(serial_number, max_retries=3):
    """
    关闭AdsPower浏览器
    
    Args:
        serial_number: 浏览器序列号
        max_retries: 最大重试次数
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    url = f"{ADSPOWER_BASE_URL}/api/v1/browser/stop"
    params = {
        "serial_number": serial_number
    }
    headers = {
        'Authorization': f'Bearer {ADSPOWER_API_KEY}'
    }
    
    for attempt in range(max_retries):
        try:
            log_print(f"[{serial_number}] 尝试关闭浏览器 (第 {attempt + 1}/{max_retries} 次)")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 0:
                log_print(f"[{serial_number}] ✓ 浏览器关闭成功")
                time.sleep(10)
                return True
            else:
                log_print(f"[{serial_number}] ✗ 关闭浏览器失败: {data.get('msg')}")
                if attempt < max_retries - 1:
                    time.sleep(10)
        except Exception as e:
            log_print(f"[{serial_number}] ✗ 关闭浏览器时发生异常: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(10)
    
    log_print(f"[{serial_number}] ✗ 最终关闭失败，已达到最大重试次数")
    return False


def create_selenium_driver(browser_data):
    """
    创建Selenium WebDriver
    
    Args:
        browser_data: AdsPower返回的浏览器数据
        
    Returns:
        WebDriver: Selenium驱动对象
    """
    chrome_driver = browser_data.get("webdriver")
    debugger_address = browser_data.get("ws", {}).get("selenium")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", debugger_address)
    
    service = Service(executable_path=chrome_driver)
    driver = webdriver.Chrome(service=service, options=options)
    
    # 设置页面加载超时时间为60秒，防止页面加载卡死导致线程无法释放
    driver.set_page_load_timeout(75)
    driver.set_script_timeout(75)
    
    return driver


# ============================================================================
# 页面操作函数
# ============================================================================

def refresh_page_with_opinion_check(driver, serial_number=""):
    """
    刷新页面前，检查当前网址是否包含 "app.opinion.trade"
    如果不包含，切换到包含 "app.opinion.trade" 的标签页，然后再刷新
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号（用于日志）
    """
    try:
        # 检查当前网址是否包含 "app.opinion.trade"
        current_url = driver.current_url
        if "app.opinion.trade" in current_url:
            # 当前页面已经是 opinion.trade，直接刷新
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ✓ 已刷新页面（当前已在 app.opinion.trade）")
            return
        
        # 当前页面不是 opinion.trade，需要切换到包含 "app.opinion.trade" 的标签页
        if serial_number:
            log_print(f"[{serial_number}] ⚠ 当前页面不是 app.opinion.trade ({current_url[:80]}...)，查找包含 app.opinion.trade 的标签页...")
        
        all_windows = driver.window_handles
        opinion_window = None
        
        # 查找包含 "app.opinion.trade" 的标签页
        for window_handle in all_windows:
            try:
                driver.switch_to.window(window_handle)
                window_url = driver.current_url
                if "app.opinion.trade" in window_url:
                    opinion_window = window_handle
                    if serial_number:
                        log_print(f"[{serial_number}] ✓ 找到 app.opinion.trade 标签页: {window_url[:80]}...")
                    break
            except Exception as e:
                # 某些标签页可能无法访问URL（如chrome://等系统页面），跳过继续查找
                continue
        
        if opinion_window:
            # 切换到 opinion.trade 标签页并刷新
            driver.switch_to.window(opinion_window)
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ✓ 已切换到 app.opinion.trade 标签页并刷新")
        else:
            # 如果没找到包含 "app.opinion.trade" 的标签页，在当前页面刷新（兜底）
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ⚠ 未找到包含 app.opinion.trade 的标签页，在当前页面刷新")
                
    except Exception as e:
        # 如果发生异常，尝试直接刷新（兜底）
        try:
            driver.refresh()
            if serial_number:
                log_print(f"[{serial_number}] ⚠ 刷新页面时发生异常，已尝试直接刷新: {str(e)}")
        except:
            if serial_number:
                log_print(f"[{serial_number}] ✗ 刷新页面失败: {str(e)}")


def check_and_click_understand_agree(driver, browser_id, timeout=5):
    """
    检查是否存在内容等于 "I Understand and Agree" 的p标签，如果存在则点击其父节点
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        timeout: 检查超时时间（秒）
        
    Returns:
        bool: 如果找到并点击了返回True，否则返回False
    """
    try:
        log_print(f"[{browser_id}] 在{timeout}秒内检查是否存在 'I Understand and Agree' p标签...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                p_tags = driver.find_elements(By.TAG_NAME, "p")
                for p in p_tags:
                    if p.text.strip() == "I Understand and Agree":
                        log_print(f"[{browser_id}] ✓ 检测到 'I Understand and Agree' p标签存在")
                        try:
                            # 获取父节点并点击
                            parent = p.find_element(By.XPATH, "..")
                            log_print(f"[{browser_id}] → 点击 'I Understand and Agree' 的父节点...")
                            parent.click()
                            log_print(f"[{browser_id}] ✓ 已点击父节点")
                            time.sleep(1)
                            return True
                        except Exception as e:
                            log_print(f"[{browser_id}] ⚠ 点击父节点时出错: {str(e)}")
                            return False
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{browser_id}] ✓ 未检测到 'I Understand and Agree' p标签")
        return False
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 检查 'I Understand and Agree' p标签时出错: {str(e)}")
        return False


def wait_for_opinion_trade_box(driver, serial_number, max_retries=3):
    """
    等待 Opinion Trade 页面加载完成，30秒内每3秒检查一次，超时刷新重试
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        max_retries: 最大重试次数
        
    Returns:
        WebElement: trade-box元素，失败返回None
    """
    for attempt in range(max_retries):
        log_print(f"[{serial_number}] [OP] 等待页面加载完成... (尝试 {attempt + 1}/{max_retries})")
        
        # 在120秒内，每3秒检查一次
        timeout = 30
        interval = 3
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                elapsed = int(time.time() - start_time)
                log_print(f"[{serial_number}] [OP] 查找 trade-box... ({elapsed}s/{timeout}s)")
                
                # 查找 trade-box
                trade_box = driver.find_element(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                
                if trade_box:
                    log_print(f"[{serial_number}] [OP] ✓ 页面加载成功，找到 trade-box (用时 {elapsed}s)")
                    return trade_box
                
            except Exception as e:
                elapsed = int(time.time() - start_time)
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 trade-box ({elapsed}s/{timeout}s)")
            
            # 等待3秒后重试
            if time.time() - start_time < timeout:
                time.sleep(interval)
        
        # 30秒超时
        log_print(f"[{serial_number}] [OP] ✗ 30秒内未找到 trade-box")
        
        if attempt < max_retries - 1:
            log_print(f"[{serial_number}] [OP] 刷新页面并重试...")
            refresh_page_with_opinion_check(driver, serial_number)
            time.sleep(2)  # 刷新后等待2秒
        else:
            log_print(f"[{serial_number}] [OP] ✗ 页面加载失败，已达到最大重试次数 ({max_retries})")
            return None
    
    return None


def check_region_restriction(driver, browser_id, timeout=3):
    """
    检查地区限制（Trading is not available to persons located in the）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        timeout: 检查超时时间（秒）
        
    Returns:
        bool: 如果检测到地区限制返回True，否则返回False
    """
    try:
        log_print(f"[{browser_id}] 检查地区限制（Trading is not available）...")
        start_time = time.time()
        trading_restricted = False
        
        while time.time() - start_time < timeout:
            try:
                # 查找所有p标签
                p_tags = driver.find_elements(By.TAG_NAME, "p")
                for p in p_tags:
                    p_text = p.text.strip()
                    if "Trading is not available to persons located in the" in p_text:
                        trading_restricted = True
                        log_print(f"[{browser_id}] ✓ 检测到地区限制提示: {p_text[:100]}...")
                        break
                if trading_restricted:
                    break
                time.sleep(0.2)  # 短暂等待后重试
            except Exception as e:
                # 查找过程中出现异常，继续循环
                time.sleep(0.2)
                continue
        
        if trading_restricted:
            log_print(f"[{browser_id}] ✗ 检测到地区限制，需要换IP")
            return True
        else:
            log_print(f"[{browser_id}] ✓ 未检测到地区限制")
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 检查地区限制时出现异常: {str(e)}，继续执行...")
        return False
    
    return False

def unlock_okx_wallet(driver, serial_number, browser_id):
    """
    检查OKX钱包是否需要解锁，如果需要则输入密码解锁
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        browser_id: 浏览器ID（用于获取密码）
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        log_print(f"[{serial_number}] 检查钱包是否需要解锁...")
        
        # 获取密码
        password = get_browser_password(browser_id)
        
        # 先尝试切换到 OKX 钱包的特定 iframe (id="ui-ses-iframe")
        try:
            log_print(f"[{serial_number}] → 查找 OKX 钱包 iframe (id='ui-ses-iframe')...")
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#ui-ses-iframe"))
            )
            driver.switch_to.frame(iframe)
            log_print(f"[{serial_number}] ✓ 已切换到 OKX 钱包 iframe")
        except TimeoutException:
            log_print(f"[{serial_number}] ℹ 未找到 ui-ses-iframe，尝试查找其他 iframe...")
            try:
                iframe = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
                )
                driver.switch_to.frame(iframe)
                log_print(f"[{serial_number}] ✓ 已切换到 iframe")
            except TimeoutException:
                log_print(f"[{serial_number}] ℹ 未找到任何 iframe，在主页面查找")
        except Exception as e:
            log_print(f"[{serial_number}] ⚠ 切换 iframe 失败: {str(e)}")
        
        # 在5秒内检查是否有密码输入框 (data-testid="okd-input")
        try:
            log_print(f"[{serial_number}] → 查找密码输入框 (data-testid='okd-input')...")
            password_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='okd-input']"))
            )
            log_print(f"[{serial_number}] ✓ 发现密码输入框，钱包需要解锁")
            
            # 使用 React 兼容的方式输入密码
            try:
                log_print(f"[{serial_number}] → 使用 React 兼容方式输入密码...")
                
                # 使用特殊的方式触发 React 的 value setter
                success = driver.execute_script("""
                    try {
                        const input = arguments[0];
                        const password = arguments[1];
                        
                        // 获取 input 的原生 value setter
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 
                            'value'
                        ).set;
                        
                        // 聚焦输入框
                        input.focus();
                        
                        // 使用原生 setter 设置值（这会触发 React 的监听）
                        nativeInputValueSetter.call(input, password);
                        
                        // 触发 input 事件（React 会监听这个）
                        const inputEvent = new Event('input', { bubbles: true });
                        input.dispatchEvent(inputEvent);
                        
                        // 触发 change 事件
                        const changeEvent = new Event('change', { bubbles: true });
                        input.dispatchEvent(changeEvent);
                        
                        return true;
                    } catch (e) {
                        console.error('输入密码失败:', e);
                        return false;
                    }
                """, password_input, password)
                
                if success:
                    log_print(f"[{serial_number}] ✓ 已输入密码（React 方式）")
                else:
                    log_print(f"[{serial_number}] ⚠ JavaScript 报告输入失败，但继续尝试")
                
            except Exception as e:
                log_print(f"[{serial_number}] ✗ 输入密码失败: {str(e)}")
                # 不抛出异常，返回 True 表示可能已解锁
                driver.switch_to.default_content()
                return True
            
            # 等待按钮从 disabled 变为可点击状态
            log_print(f"[{serial_number}] → 等待解锁按钮变为可点击状态...")
            time.sleep(1)
            
            # 在10秒内找到并等待解锁按钮变为可点击 (去掉 disabled 属性)
            try:
                log_print(f"[{serial_number}] → 查找解锁按钮 (data-testid='okd-button')...")
                # 等待按钮可点击（没有 disabled 属性）
                unlock_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='okd-button']"))
                )
                log_print(f"[{serial_number}] ✓ 解锁按钮已启用")
                
                log_print(f"[{serial_number}] → 点击解锁按钮...")
                unlock_button.click()
                log_print(f"[{serial_number}] ✓ 已点击解锁按钮")
                
                # 等待解锁完成
                time.sleep(2)
                
                # 切换回主页面
                driver.switch_to.default_content()
                log_print(f"[{serial_number}] ✓ 已切换回主页面")
                
                return True
            except TimeoutException:
                # 切换回主页面
                driver.switch_to.default_content()
                log_print(f"[{serial_number}] ✗ 未找到解锁按钮")
                return False
                
        except TimeoutException:
            # 切换回主页面
            try:
                driver.switch_to.default_content()
            except:
                pass
            log_print(f"[{serial_number}] ℹ 未发现密码输入框，钱包可能已解锁")
            return True
            
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 检查/解锁钱包时出错: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] 错误详情:\n{traceback.format_exc()}")
        return False



def open_new_tab_with_url(driver, url, serial_number):
    """
    在新标签页中打开URL
    
    Args:
        driver: Selenium WebDriver对象
        url: 要打开的URL
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        # 获取当前窗口句柄
        current_window = driver.current_window_handle
        original_window_count = len(driver.window_handles)
        
        # 方法1: 使用 driver.switch_to.new_window (Selenium 4+)
        try:
            driver.switch_to.new_window('tab')
            time.sleep(1)
            driver.get(url)
            time.sleep(2)
            log_print(f"[{serial_number}] ✓ 已在新标签页打开: {url}")
            return True
        except Exception as e1:
            log_print(f"[{serial_number}] ⚠ new_window 方法失败: {str(e1)}，尝试 Ctrl+T...")
            # 切换回原窗口
            try:
                driver.switch_to.window(current_window)
            except:
                pass
        
        # 方法2: 使用 Ctrl+T 打开新标签页，然后用 driver.get() 导航
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.CONTROL + 't')
            time.sleep(1)
            
            # 切换到新标签页
            all_windows = driver.window_handles
            if len(all_windows) > original_window_count:
                new_window = all_windows[-1]
                driver.switch_to.window(new_window)
                
                # 使用 driver.get() 导航（比JavaScript更可靠）
                driver.get(url)
                time.sleep(2)
                
                log_print(f"[{serial_number}] ✓ 已在新标签页打开 (Ctrl+T): {url}")
                return True
        except Exception as e2:
            log_print(f"[{serial_number}] ⚠ Ctrl+T 方法失败: {str(e2)}")
        
        return False
    except Exception as e:
        log_print(f"[{serial_number}] ✗ 打开新标签页失败: {str(e)}")
        return False
    

def preopen_okx_wallet(driver, serial_number, current_ip=None, current_delay=None):
    """
    预先打开OKX钱包页面，解锁钱包并处理所有待确认的弹窗
    
    Args:
        driver: Selenium WebDriver对象
        serial_number: 浏览器序列号
        current_ip: 当前使用的IP地址（可选）
        current_delay: 当前IP的延迟（可选，单位：毫秒）
        
    Returns:
        str: 主窗口句柄
    """
    log_print(f"[{serial_number}] [预处理] 检查并预打开 OKX 钱包页面...")
    
    # 保存主窗口句柄
    main_window = driver.current_window_handle
    
    # 先预打开 beijing_time.html 页面
    try:
        log_print(f"[{serial_number}] → 预打开 beijing_time.html 页面...")
        
        # 构建URL，包含IP和延迟参数
        beijing_time_url = f"https://oss.w3id.info/OpsStatistics/beijing_time.html?browser={serial_number}"
        if current_ip:
            beijing_time_url += f"&ip={current_ip}"
        if current_delay is not None:
            beijing_time_url += f"&delay={current_delay}"
        
        success = open_new_tab_with_url(driver, beijing_time_url, serial_number)
        if success:
            log_print(f"[{serial_number}] ✓ beijing_time.html 页面已打开")
        else:
            log_print(f"[{serial_number}] ⚠ 预打开 beijing_time.html 失败，继续执行...")
        # 切换回主窗口
        driver.switch_to.window(main_window)
        time.sleep(1)
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 预打开 beijing_time.html 异常: {str(e)}，继续执行...")
        try:
            driver.switch_to.window(main_window)
        except:
            pass
    
    okx_extension_id = "mcohilncbfahbmgdjkbpemcciiolgcge"
    okx_popup_url = f"chrome-extension://{okx_extension_id}/popup.html"
    okx_window = None
    
    try:
        # 检查是否已经存在OKX钱包标签页
        log_print(f"[{serial_number}] → 检查是否已存在 OKX 钱包标签页...")
        all_windows = driver.window_handles
        okx_window_exists = False
        
        for window in all_windows:
            try:
                # 暂时切换到该窗口检查URL
                driver.switch_to.window(window)
                current_url = driver.current_url
                
                # 检查是否包含OKX扩展ID
                if okx_extension_id in current_url:
                    okx_window_exists = True
                    okx_window = window
                    log_print(f"[{serial_number}] ✓ 已找到现有的 OKX 钱包标签页: {current_url}")
                    break
            except Exception as e:
                # 某些窗口可能无法访问，继续检查下一个
                continue
        
        # 切换回主窗口
        driver.switch_to.window(main_window)
        
        # 如果不存在OKX窗口，则打开新的
        if not okx_window_exists:
            log_print(f"[{serial_number}] → 未找到 OKX 钱包标签页，正在打开...")
            success = open_new_tab_with_url(driver, okx_popup_url, serial_number)
            
            if success:
                log_print(f"[{serial_number}] ✓ OKX 钱包页面已打开")
                # 获取新打开的OKX窗口
                all_windows = driver.window_handles
                for window in all_windows:
                    if window != main_window:
                        try:
                            driver.switch_to.window(window)
                            if okx_extension_id in driver.current_url:
                                okx_window = window
                                break
                        except:
                            continue
            else:
                log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包失败，继续执行...")
                time.sleep(3)
        else:
            log_print(f"[{serial_number}] ✓ 使用现有的 OKX 钱包标签页")
        
        # 如果找到了OKX窗口，进行解锁和处理确认按钮
        if okx_window:
            try:
                # 切换到OKX窗口
                driver.switch_to.window(okx_window)
                log_print(f"[{serial_number}] → 切换到 OKX 钱包窗口进行解锁...")
                
                # 先解锁钱包
                unlock_okx_wallet(driver, serial_number, serial_number)
                
                # 在10秒内循环查找并点击确认按钮
                log_print(f"[{serial_number}] → 开始查找并处理确认按钮（10秒超时）...")
                start_time = time.time()
                buttons_clicked = 0
                
                while time.time() - start_time < 15:
                    try:
                        confirm_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                        if confirm_buttons and len(confirm_buttons) > 0:
                            # 点击第一个按钮
                            confirm_buttons[0].click()
                            buttons_clicked += 1
                            log_print(f"[{serial_number}] ✓ 已点击第 {buttons_clicked} 个确认按钮")
                            time.sleep(0.5)  # 等待页面响应
                        else:
                            # 没有找到按钮，检查是否已经处理完毕
                            if buttons_clicked > 0:
                                log_print(f"[{serial_number}] ✓ 所有确认按钮已处理完毕，共点击 {buttons_clicked} 个")
                            else:
                                log_print(f"[{serial_number}] → 未找到确认按钮")
                            break
                    except Exception as e:
                        log_print(f"[{serial_number}] ⚠ 查找按钮时出错: {str(e)}")
                        time.sleep(0.5)
                
                if time.time() - start_time >= 10:
                    log_print(f"[{serial_number}] ⚠ 处理确认按钮超时（10秒），共点击 {buttons_clicked} 个")
                    
            except Exception as e:
                log_print(f"[{serial_number}] ⚠ 处理 OKX 钱包时出错: {str(e)}")
        
        # 切换回主窗口
        log_print(f"[{serial_number}] → 切换回主窗口")
        driver.switch_to.window(main_window)
        log_print(f"[{serial_number}] ✓ 已切换回主窗口")
        
        # 等待1秒
        time.sleep(1)
        
    except Exception as e:
        log_print(f"[{serial_number}] ⚠ 预打开 OKX 钱包异常: {str(e)}，继续执行...")
        try:
            driver.switch_to.window(main_window)
        except:
            pass
    
    return main_window

def connect_wallet_if_needed(driver, browser_id):
    """
    检查并连接钱包（如果需要）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{browser_id}] 在10秒内检查是否需要连接钱包...")
        time.sleep(10)
        # 在10秒内查找是否有 "Connect Wallet" 按钮或 "OKX Wallet" 的 p 标签
        connect_wallet_button = None
        okx_wallet_p = None
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                # 查找 Connect Wallet 按钮
                connect_buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in connect_buttons:
                    if button.text.strip() == "Connect Wallet":
                        connect_wallet_button = button
                        log_print(f"[{browser_id}] ✓ 找到 Connect Wallet 按钮")
                        break
                
                # 查找 OKX Wallet 的 p 标签
                if not connect_wallet_button:
                    p_tags = driver.find_elements(By.TAG_NAME, "p")
                    for p in p_tags:
                        if p.text.strip() == "OKX Wallet":
                            okx_wallet_p = p
                            log_print(f"[{browser_id}] ✓ 找到 OKX Wallet 选项")
                            break
                
                # 如果找到了其中一个，停止查找
                if connect_wallet_button or okx_wallet_p:
                    break
                
                # 如果3秒后两个都没找到，认为已连接
                if time.time() - start_time > 3:
                    log_print(f"[{browser_id}] ✓ 未找到 Connect Wallet 按钮和 OKX Wallet 选项，钱包已连接")
                    return True
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        # 10秒后，检查结果
        if not connect_wallet_button and not okx_wallet_p:
            log_print(f"[{browser_id}] ✓ 未找到 Connect Wallet 按钮和 OKX Wallet 选项，钱包已连接")
            return True
        
        # 如果有 Connect Wallet 按钮，点击它
        if connect_wallet_button:
            log_print(f"[{browser_id}] → 点击 Connect Wallet 按钮...")
            connect_wallet_button.click()
            time.sleep(1)
            
            # 点击后需要查找 OKX Wallet 选项
            okx_wallet_p = None
        
        # 如果还没有找到 OKX Wallet 选项，在10秒内查找
        if not okx_wallet_p:
            log_print(f"[{browser_id}] → 在10秒内查找 OKX Wallet 选项...")
            start_time = time.time()
            
            while time.time() - start_time < 10:
                try:
                    p_tags = driver.find_elements(By.TAG_NAME, "p")
                    
                    for p in p_tags:
                        if p.text.strip() == "OKX Wallet":
                            okx_wallet_p = p
                            log_print(f"[{browser_id}] ✓ 找到 OKX Wallet 选项")
                            break
                    
                    if okx_wallet_p:
                        break
                    
                    time.sleep(0.5)
                except:
                    time.sleep(0.5)
        
        # 如果找到了 OKX Wallet 选项，点击它
        if okx_wallet_p:
            try:
                log_print(f"[{browser_id}] → 点击 OKX Wallet 选项...")
                # 点击父节点的父节点
                parent_parent = okx_wallet_p.find_element(By.XPATH, "../..")
                parent_parent.click()
                log_print(f"[{browser_id}] ✓ 已点击 OKX Wallet")
                time.sleep(2)
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ 点击 OKX Wallet 失败: {str(e)}")
                return True  # 继续执行
        else:
            log_print(f"[{browser_id}] ⚠ 10秒内未找到 OKX Wallet 选项")
            return True  # 继续执行
        
        # 切换到 OKX 窗口
        log_print(f"[{browser_id}] → 切换到 OKX 窗口...")
        main_window = driver.current_window_handle
        all_windows = driver.window_handles
        
        okx_window = None
        for window in all_windows:
            if window != main_window:
                driver.switch_to.window(window)
                if "okx" in driver.current_url.lower() or "mcohilncbfahbmgdjkbpemcciiolgcge" in driver.current_url:
                    okx_window = window
                    log_print(f"[{browser_id}] ✓ 找到 OKX 窗口")
                    break
        
        if okx_window:
            # 解锁 OKX 钱包
            log_print(f"[{browser_id}] → 解锁 OKX 钱包...")
            unlock_okx_wallet(driver, browser_id, browser_id)
            
            # 在10秒内等待并点击确认按钮（第二个按钮）
            log_print(f"[{browser_id}] → 查找确认按钮（10秒超时）...")
            start_time = time.time()
            button_clicked = False
            
            while time.time() - start_time < 10:
                try:
                    confirm_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                    if len(confirm_buttons) >= 2:
                        confirm_buttons[1].click()
                        log_print(f"[{browser_id}] ✓ 已点击确认按钮（第二个）")
                        button_clicked = True
                        break
                    else:
                        time.sleep(0.5)  # 等待后重试
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ 查找按钮时出错: {str(e)}")
                    time.sleep(0.5)
            
            if not button_clicked:
                log_print(f"[{browser_id}] ⚠ 未找到足够的确认按钮或超时")
            
            # 切换回主窗口
            driver.switch_to.window(main_window)
            log_print(f"[{browser_id}] ✓ 已切换回主窗口")
        
        return True
        
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 连接钱包失败: {str(e)}")
        return True  # 即使失败也继续执行


def check_api_restriction(driver, browser_id, timeout=3):
    """
    检测是否出现API is not available to persons located in the
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        timeout: 检查超时时间（秒）
        
    Returns:
        bool: 如果检测到API限制返回True，否则返回False
    """
    log_print(f"[{browser_id}] 检查API限制...")
    try:
        start_time = time.time()
        region_restricted = False
        
        while time.time() - start_time < timeout:
            try:
                # 查找所有div元素
                all_divs = driver.find_elements(By.TAG_NAME, "div")
                for div in all_divs:
                    div_text = div.text
                    if "API is not available to persons located in the" in div_text:
                        region_restricted = True
                        log_print(f"[{browser_id}] ✓ 检测到API限制提示: {div_text[:100]}...")
                        break
                if region_restricted:
                    break
                time.sleep(0.2)  # 短暂等待后重试
            except Exception as e:
                # 查找过程中出现异常，继续循环
                time.sleep(0.2)
                continue
        
        if region_restricted:
            log_print(f"[{browser_id}] ✗ IP通畅，但地区不符合")
            return True
        else:
            log_print(f"[{browser_id}] ✓ 未检测到地区限制")
    except Exception as e:
        log_print(f"[{browser_id}] ⚠ 检查地区限制时出现异常: {str(e)}，继续执行...")
        return False
    
    return False


def wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
    """
    等待Position按钮出现，如果没有则重新加载页面并重试
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        max_retries: 最大重试次数
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    log_print(f"[{browser_id}] 从OKX切换回来，等待3秒...")
    time.sleep(3)
    
    for retry in range(max_retries + 1):
        if retry > 0:
            log_print(f"[{browser_id}] 第 {retry} 次重试...")
        
        # 在10秒内查找Position按钮
        log_print(f"[{browser_id}] 在10秒内查找Position按钮...")
        start_time = time.time()
        position_button_found = False
        
        while time.time() - start_time < 10:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.text.strip() == "Position":
                        position_button_found = True
                        log_print(f"[{browser_id}] ✓ 找到Position按钮")
                        return True
                
                time.sleep(0.5)  # 每0.5秒检查一次
                
            except Exception as e:
                log_print(f"[{browser_id}] 查找按钮时出错: {str(e)}")
                time.sleep(0.5)
        
        # 10秒后还没找到Position按钮
        if not position_button_found:
            if retry < max_retries:
                log_print(f"[{browser_id}] ⚠ 10秒后仍未找到Position按钮，重新加载页面...")
                refresh_page_with_opinion_check(driver, browser_id)
                time.sleep(2)
                
                # 重新检查并连接钱包
                log_print(f"[{browser_id}] 重新检查并连接钱包...")
                connect_wallet_if_needed(driver, browser_id)
            else:
                log_print(f"[{browser_id}] ✗ 未找到Position按钮，已达到最大重试次数")
                return False
    
    return False


def click_opinion_trade_type_button(trade_box, trade_type, serial_number):
    """
    点击 Opinion Trade 的买卖方向按钮
    
    Args:
        trade_box: trade-box元素
        trade_type: "Buy" 或 "Sell"
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并点击 {trade_type} 按钮...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                buttons = trade_box.find_elements(By.TAG_NAME, "button")
                
                for button in buttons:
                    if button.text.strip() == trade_type:
                        button.click()
                        log_print(f"[{serial_number}] [OP] ✓ 已点击 {trade_type} 按钮")
                        time.sleep(0.5)
                        return True
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到 {trade_type} 按钮")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 {trade_type} 按钮失败: {str(e)}")
        return False


def select_opinion_price_type(trade_box, price_type, serial_number):
    """
    选择 Opinion Trade 的价格类型
    
    Args:
        trade_box: trade-box元素
        price_type: "Market" 或 "Limit"
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找价格类型 {price_type}...")
        
        p_tags = trade_box.find_elements(By.TAG_NAME, "p")
        
        target_p = None
        other_price_type = "Market" if price_type == "Limit" else "Limit"
        other_p = None
        
        for p in p_tags:
            text = p.text.strip()
            if text == price_type:
                target_p = p
                break
            elif text == other_price_type:
                other_p = p
        
        if target_p:
            log_print(f"[{serial_number}] [OP] ✓ 找到目标价格类型 {price_type}")
            return True
        elif other_p:
            log_print(f"[{serial_number}] [OP] 未找到 {price_type}，点击 {other_price_type} 切换...")
            parent = other_p.find_element(By.XPATH, "..")
            parent.click()
            time.sleep(0.5)
            log_print(f"[{serial_number}] [OP] ✓ 已点击切换到 {price_type}")
            return True
        else:
            log_print(f"[{serial_number}] [OP] ✗ 未找到任何价格类型标签")
            return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 选择价格类型失败: {str(e)}")
        return False


def select_opinion_option_type(trade_box, option_type, serial_number):
    """
    选择 Opinion Trade 的种类
    
    Args:
        trade_box: trade-box元素
        option_type: "YES" 或 "NO"
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 在10秒内查找并选择种类 {option_type}...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                # 查找所有具有特定属性的 button
                buttons = trade_box.find_elements(By.CSS_SELECTOR, 'button[data-sentry-element="Button"][data-sentry-source-file="BuySell.tsx"]')
                
                if len(buttons) >= 2:
                    # YES = 第一个按钮，NO = 第二个按钮
                    button_index = 0 if option_type == "YES" else 1
                    target_button = buttons[button_index]
                    
                    log_print(f"[{serial_number}] [OP] ✓ 找到 {option_type} 按钮（第 {button_index + 1} 个）")
                    
                    target_button.click()
                    log_print(f"[{serial_number}] [OP] ✓ 已点击 {option_type} 选项")
                    time.sleep(0.5)
                    
                    # 检查是否激活
                    active_attr = target_button.get_attribute("data-active")
                    if active_attr == "true":
                        log_print(f"[{serial_number}] [OP] ✓ {option_type} 选项已激活")
                        return True
                    else:
                        log_print(f"[{serial_number}] [OP] ⚠ {option_type} 选项未激活")
                        return False
                
                time.sleep(0.5)
            except:
                time.sleep(0.5)
        
        log_print(f"[{serial_number}] [OP] ✗ 10秒内未找到足够的按钮")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 选择种类失败: {str(e)}")
        return False


def click_opinion_amount_tab(trade_box, serial_number):
    """
    点击 Opinion Trade 的 Amount 标签
    
    Args:
        trade_box: trade-box元素
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找 Amount 标签...")
        
        # 查找所有可能的标签元素
        tabs = trade_box.find_elements(By.CSS_SELECTOR, '[role="tab"]')
        for tab in tabs:
            if "Amount" in tab.text or "amount" in tab.text.lower():
                log_print(f"[{serial_number}] [OP] ✓ 找到 Amount 标签")
                tab.click()
                log_print(f"[{serial_number}] [OP] ✓ 已点击 Amount 标签")
                time.sleep(0.5)
                return True
        
        # 如果没找到，尝试查找p标签
        p_tags = trade_box.find_elements(By.TAG_NAME, "p")
        for p in p_tags:
            if "Amount" in p.text or "amount" in p.text.lower():
                log_print(f"[{serial_number}] [OP] ✓ 找到 Amount 标签（p标签）")
                parent = p.find_element(By.XPATH, "..")
                parent.click()
                log_print(f"[{serial_number}] [OP] ✓ 已点击 Amount 标签")
                time.sleep(0.5)
                return True
        
        log_print(f"[{serial_number}] [OP] ⚠ 未找到 Amount 标签，继续执行...")
        return False
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 点击 Amount 标签失败: {str(e)}，继续执行...")
        return False


def fill_opinion_price_and_amount(trade_box, price, amount, serial_number):
    """
    填入 Opinion Trade 的价格和数量
    
    Args:
        trade_box: trade-box元素
        price: 价格（Limit模式）
        amount: 数量
        serial_number: 浏览器序列号
        
    Returns:
        bool: 成功返回True
    """
    try:
        inputs = trade_box.find_elements(By.TAG_NAME, "input")
        
        log_print(f"[{serial_number}] [OP] 在 trade-box 下找到 {len(inputs)} 个 input 元素")
        
        if len(inputs) == 0:
            log_print(f"[{serial_number}] [OP] ✗ 未找到任何 input 元素")
            return False
        
        # Limit模式：填入价格和数量到前两个input
        if len(inputs) < 2:
            log_print(f"[{serial_number}] [OP] ✗ Limit模式需要至少2个input，但只找到 {len(inputs)} 个")
            return False
        
        log_print(f"[{serial_number}] [OP] Limit模式，填入价格和数量...")
        
        # 第一个input填价格
        price_input = inputs[0]
        price_input.clear()
        price_input.send_keys(str(price))
        log_print(f"[{serial_number}] [OP] ✓ 已填入价格: {price}")
        time.sleep(0.3)
        
        # 第二个input填数量
        amount_input = inputs[1]
        amount_input.clear()
        amount_input.send_keys(str(amount))
        log_print(f"[{serial_number}] [OP] ✓ 已填入数量: {amount}")
        time.sleep(0.3)
        
        return True
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 填入价格/数量失败: {str(e)}")
        return False


def submit_opinion_order(driver, trade_box, trade_type, option_type, serial_number, browser_id, task_data=None):
    """
    提交 Opinion Trade 订单
    
    Args:
        driver: Selenium WebDriver对象
        trade_box: trade-box元素
        trade_type: 买卖类型
        option_type: 种类
        serial_number: 浏览器序列号
        browser_id: 浏览器ID
        task_data: 任务数据（用于type=5的同步机制）
        
    Returns:
        tuple: (success, should_retry_or_msg)
            - (True, True): 成功
            - (False, True): 失败，可以重试
            - (False, False): 失败，不应重试（如type=5点击取消）
            - (False, "msg"): 失败，不应重试，并带有具体失败原因
    """
    try:
        log_print(f"[{serial_number}] [OP] 查找提交订单按钮...")
        
        p_tags = trade_box.find_elements(By.TAG_NAME, "p")
        
        for p in p_tags:
            text = p.text.strip()
            if trade_type in text:
                log_print(f"[{serial_number}] [OP] ✓ 找到提交按钮，文本: {text}")
                
                parent = p.find_element(By.XPATH, "..")
                parent.click()
                log_print(f"[{serial_number}] [OP] ✓ 已点击提交订单按钮")
                
                # 在3秒内检查是否有"Unusual Limit Price"提示
                log_print(f"[{serial_number}] [OP] 检查限价提示...")
                start_time = time.time()
                unusual_limit_found = False
                
                while time.time() - start_time < 3:
                    try:
                        # 查找所有h2标签
                        h2_tags = driver.find_elements(By.TAG_NAME, "h2")
                        for h2 in h2_tags:
                            h2_text = h2.text.strip()
                            if "Unusual Limit Price" in h2_text:
                                unusual_limit_found = True
                                log_print(f"[{serial_number}] [OP] ✗ 检测到限价提示: {h2_text}")
                                break
                        if unusual_limit_found:
                            break
                        time.sleep(0.2)  # 短暂等待后重试
                    except Exception as e:
                        # 查找过程中出现异常，继续尝试
                        time.sleep(0.2)
                        continue
                
                if unusual_limit_found:
                    log_print(f"[{serial_number}] [OP] ✗ 限价距离市价差距过大")
                    return False, "限价距离市价差距过大"
                
                log_print(f"[{serial_number}] [OP] ✓ 未检测到限价提示，继续执行...")
                
                # 检查是否需要点击 Confirm 按钮
                log_print(f"[{serial_number}] [OP] 检查是否需要点击 Confirm 按钮...")
                confirm_clicked = False
                start_time_confirm = time.time()
                
                while time.time() - start_time_confirm < 4:
                    try:
                        # 查找所有 h2、div、p 标签
                        all_elements = []
                        all_elements.extend(driver.find_elements(By.TAG_NAME, "h2"))
                        all_elements.extend(driver.find_elements(By.TAG_NAME, "div"))
                        all_elements.extend(driver.find_elements(By.TAG_NAME, "p"))
                        
                        found_secure_trade = False
                        for element in all_elements:
                            element_text = element.text.strip()
                            if "Securely trade on opinion.trade on" in element_text:
                                found_secure_trade = True
                                log_print(f"[{serial_number}] [OP] ✓ 检测到安全交易提示")
                                break
                        
                        if found_secure_trade:
                            # 查找内容等于 "Confirm" 的 button
                            all_buttons = driver.find_elements(By.TAG_NAME, "button")
                            for button in all_buttons:
                                if button.text.strip() == "Confirm":
                                    log_print(f"[{serial_number}] [OP] ✓ 找到 Confirm 按钮，点击...")
                                    button.click()
                                    confirm_clicked = True
                                    log_print(f"[{serial_number}] [OP] ✓ 已点击 Confirm 按钮")
                                    break
                            
                            if confirm_clicked:
                                break
                        
                        time.sleep(0.2)
                    except Exception as e:
                        log_print(f"[{serial_number}] [OP] ⚠ 检查 Confirm 按钮时出现异常: {str(e)}")
                        time.sleep(0.2)
                        continue
                
                if not confirm_clicked:
                    log_print(f"[{serial_number}] [OP] ✓ 未检测到需要点击 Confirm 的情况")
                
                # 切换到OKX页面
                log_print(f"[{serial_number}] [OP] 切换到 OKX 钱包页面...")
                all_windows = driver.window_handles
                
                for window in all_windows:
                    driver.switch_to.window(window)
                    current_url = driver.current_url
                    if "chrome-extension://" in current_url and "mcohilncbfahbmgdjkbpemcciiolgcge" in current_url:
                        log_print(f"[{serial_number}] [OP] ✓ 已切换到 OKX 页面")
                        
                        # 点击确认按钮
                        log_print(f"[{serial_number}] [OP] 查找确认按钮...")
                        time.sleep(3)
                        buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="okd-button"]')
                        
                        if len(buttons) >= 2:
                            # 检查第二个按钮（确认按钮）是否被禁用
                            
                            # 普通任务（Type 1），直接点击确认
                            buttons[0].click()
                            log_print(f"[{serial_number}] [OP] ✓ 已点击 OKX 确认按钮")
                            
                            # 切回主页面
                            time.sleep(1)
                            for window2 in driver.window_handles:
                                driver.switch_to.window(window2)
                                if "app.opinion.trade" in driver.current_url:
                                    log_print(f"[{serial_number}] [OP] ✓ 已切回主页面")
                                    return True, True  # 成功
                        else:
                            log_print(f"[{serial_number}] [OP] ⚠ OKX 按钮数量不足: {len(buttons)}")
                            # 切回主页面
                            for window2 in driver.window_handles:
                                driver.switch_to.window(window2)
                                if "app.opinion.trade" in driver.current_url:
                                    break
                            return False, True  # 失败，可重试
                
                log_print(f"[{serial_number}] [OP] ⚠ 未找到 OKX 页面")
                return False, True  # 失败，可重试
        
        log_print(f"[{serial_number}] [OP] ✗ 未找到提交订单按钮")
        return False, True  # 失败，可重试
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 提交订单失败: {str(e)}")
        return False, True  # 失败，可重试


def submit_opinion_order_simple(driver, trade_box, browser_id, serial_number):
    """
    提交Opinion Trade订单（用于IP测试的包装函数）
    设置买卖方向为"Buy"，买卖类型为"YES"，价格类型为"Limit"，价格为10，数量为100
    
    Args:
        driver: Selenium WebDriver对象
        trade_box: trade-box元素
        browser_id: 浏览器ID
        serial_number: 浏览器序列号
        
    Returns:
        tuple: (success, failure_reason)
            - (True, None): 成功
            - (False, reason): 失败，带有失败原因
    """
    try:
        log_print(f"[{serial_number}] [OP] 开始设置订单参数...")
        
        # 1. 设置买卖方向为"Buy"
        if not click_opinion_trade_type_button(trade_box, "Buy", serial_number):
            log_print(f"[{serial_number}] [OP] ✗ 设置买卖方向失败")
            return False, "8"
        
        # 2. 设置价格类型为"Limit"
        if not select_opinion_price_type(trade_box, "Limit", serial_number):
            log_print(f"[{serial_number}] [OP] ✗ 设置价格类型失败")
            return False, "8"
        
        # 3. 设置买卖类型为"YES"
        if not select_opinion_option_type(trade_box, "YES", serial_number):
            log_print(f"[{serial_number}] [OP] ✗ 设置买卖类型失败")
            return False, "8"
        
        # 4. 点击Amount标签
        click_opinion_amount_tab(trade_box, serial_number)
        
        # 5. 填入价格和数量
        price = random.randint(10, 15)
        amount = random.randint(100, 200)
        if not fill_opinion_price_and_amount(trade_box, price, amount, serial_number):
            log_print(f"[{serial_number}] [OP] ✗ 填入价格/数量失败")
            return False, "8"
        
        # 6. 调用完整的submit_opinion_order方法
        success, result = submit_opinion_order(driver, trade_box, "Buy", "YES", serial_number, browser_id, task_data=None)
        
        if success:
            return True, None
        else:
            # 转换失败原因
            if result == True:
                return False, "8"  # 可重试的失败
            elif isinstance(result, str):
                if "限价" in result or "Unusual" in result:
                    return True, None
                elif "okx" in result.lower():
                    return True, None
                else:
                    return False, "8"
            else:
                return False, "8"
        
    except Exception as e:
        log_print(f"[{serial_number}] [OP] ✗ 提交订单失败: {str(e)}")
        import traceback
        log_print(f"[{serial_number}] [OP] 异常详情:\n{traceback.format_exc()}")
        return False, "8"


def get_balance_spot_address(driver, browser_id, timeout=30):
    """
    获取 Balance Spot 的地址（通过点击按钮并读取剪切板）
    
    Args:
        driver: Selenium WebDriver对象
        browser_id: 浏览器ID
        timeout: 超时时间（秒），默认30秒，但实际使用45秒
        
    Returns:
        tuple: (地址字符串, 是否成功)
            - 如果成功获取到0x开头的地址: (address, True)
            - 如果失败: (None, False)
    """
    try:
        log_print(f"[{browser_id}] 等待包含 'Balance Spot' 的 P 标签出现（最多等待60秒）...")
        
        # 1. 在60秒内等待包含 "Balance Spot" 的 P 标签出现
        try:
            target_p = WebDriverWait(driver, 45).until(
                lambda d: next(
                    (p for p in d.find_elements(By.TAG_NAME, "p")
                     if "Balance Spot" in p.text.strip()),
                    None
                )
            )
            log_print(f"[{browser_id}] ✓ 找到包含 'Balance Spot' 的 P 标签")
        except Exception as e:
            log_print(f"[{browser_id}] ⚠ 60秒内未找到包含 'Balance Spot' 的 P 标签: {str(e)}")
            return None, False
        
        # 2. 找到 P 标签的父节点
        parent = target_p.find_element(By.XPATH, "..")
        log_print(f"[{browser_id}] ✓ 找到父节点")
        
        # 3. 从父节点中找到 button
        buttons = parent.find_elements(By.TAG_NAME, "button")
        if not buttons:
            log_print(f"[{browser_id}] ⚠ 父节点中未找到 button")
            return None, False
        
        target_button = buttons[0]
        log_print(f"[{browser_id}] ✓ 找到 button，准备点击...")
        
        # 4. 点击 button
        target_button.click()
        log_print(f"[{browser_id}] ✓ 已点击 button")
        
        # 5. 等待一小段时间，确保剪切板内容已更新
        time.sleep(0.5)
        
        # 6. 获取剪切板内容
        clipboard_content = None
        try:
            # 优先尝试使用 pyperclip
            try:
                import pyperclip
                clipboard_content = pyperclip.paste()
                log_print(f"[{browser_id}] ✓ 使用 pyperclip 获取剪切板内容")
            except ImportError:
                # 如果没有 pyperclip，尝试使用 Windows API
                try:
                    import win32clipboard
                    win32clipboard.OpenClipboard()
                    try:
                        clipboard_content = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                        if isinstance(clipboard_content, bytes):
                            clipboard_content = clipboard_content.decode('utf-8', errors='ignore')
                        log_print(f"[{browser_id}] ✓ 使用 win32clipboard 获取剪切板内容")
                    finally:
                        win32clipboard.CloseClipboard()
                except ImportError:
                    log_print(f"[{browser_id}] ⚠ 未安装 pyperclip 或 pywin32，无法获取剪切板内容")
                    return None, False
                except Exception as e:
                    log_print(f"[{browser_id}] ⚠ win32clipboard 获取失败: {str(e)}")
                    return None, False
            except Exception as e:
                log_print(f"[{browser_id}] ⚠ pyperclip 获取失败: {str(e)}")
                return None, False
            
            if not clipboard_content:
                log_print(f"[{browser_id}] ⚠ 剪切板内容为空")
                return None, False
            
            log_print(f"[{browser_id}] 剪切板内容: {clipboard_content}")
            
            # 7. 验证是否是 0x 开头的地址
            clipboard_content = clipboard_content.strip()
            if clipboard_content.startswith('0x'):
                address = clipboard_content
                log_print(f"[{browser_id}] ✓ 成功获取到地址: {address}")
                return address, True
            else:
                log_print(f"[{browser_id}] ⚠ 剪切板内容不是有效的地址格式（不是0x开头）")
                return None, False
                
        except Exception as e:
            log_print(f"[{browser_id}] ✗ 获取剪切板内容失败: {str(e)}")
            import traceback
            log_print(f"[{browser_id}] 错误详情:\n{traceback.format_exc()}")
            return None, False
        
    except Exception as e:
        log_print(f"[{browser_id}] ✗ 获取 Balance Spot 地址时发生异常: {str(e)}")
        import traceback
        log_print(f"[{browser_id}] 异常详情:\n{traceback.format_exc()}")
        return None, False


# ============================================================================
# 主处理函数
# ============================================================================

def get_browser_lock(browser_id):
    """
    获取指定浏览器ID的锁，如果不存在则创建
    
    Args:
        browser_id: 浏览器ID
        
    Returns:
        threading.Lock: 浏览器ID对应的锁
    """
    with BROWSER_LOCKS_LOCK:
        if browser_id not in BROWSER_LOCKS:
            BROWSER_LOCKS[browser_id] = threading.Lock()
        return BROWSER_LOCKS[browser_id]


def process_ip_queue(browser_id):
    """
    处理指定浏览器ID的IP队列（串行处理）
    
    Args:
        browser_id: 浏览器ID
    """
    while True:
        # 从队列中获取IP
        ip_info = None
        with BROWSER_QUEUES_LOCK:
            if browser_id in BROWSER_QUEUES and BROWSER_QUEUES[browser_id]:
                ip_info = BROWSER_QUEUES[browser_id].pop(0)
            else:
                # 队列为空，标记为不再处理
                with BROWSER_PROCESSING_LOCK:
                    BROWSER_PROCESSING[browser_id] = False
                break
        
        if ip_info:
            # 处理这个IP
            process_ip_internal(ip_info)


def process_ip(ip_info):
    """
    处理单个IP的完整流程（会检查浏览器ID是否正在处理，如果是则加入队列）
    
    Args:
        ip_info: IP信息字典
    """
    ip = ip_info.get("ip", "unknown")
    browser_id = ip_info.get("number", "unknown")
    log_prefix = f"[{browser_id}-{ip}]"
    
    # 检查这个浏览器ID是否正在处理
    with BROWSER_PROCESSING_LOCK:
        if browser_id in BROWSER_PROCESSING and BROWSER_PROCESSING[browser_id]:
            # 正在处理，加入队列
            with BROWSER_QUEUES_LOCK:
                if browser_id not in BROWSER_QUEUES:
                    BROWSER_QUEUES[browser_id] = []
                BROWSER_QUEUES[browser_id].append(ip_info)
            log_print(f"{log_prefix} 浏览器ID {browser_id} 正在处理其他IP，已加入队列（队列长度: {len(BROWSER_QUEUES[browser_id])}）")
            return
        else:
            # 标记为正在处理
            BROWSER_PROCESSING[browser_id] = True
    
    # 直接处理这个IP
    process_ip_internal(ip_info)
    
    # 处理完成后，继续处理队列中的IP（串行）
    process_ip_queue(browser_id)


def process_ip_internal(ip_info):
    """
    实际处理单个IP的完整流程
    
    Args:
        ip_info: IP信息字典
    """
    ip = ip_info.get("ip", "unknown")
    browser_id = ip_info.get("number", "unknown")
    serial_number = browser_id
    log_prefix = f"[{browser_id}-{ip}]"
    
    try:
        log_print(f"\n{'='*80}")
        log_print(f"{log_prefix} 开始处理IP: {ip}, 浏览器ID: {browser_id}")
        log_print(f"{'='*80}\n")
    
        # 初始化结果数据
        result_data = ip_info.copy()
        
        # 解析原有数据
        original_a = ip_info.get("a")  # 完成时间戳
        original_b = ip_info.get("b", "")  # http模式 "成功次数,失败次数"
        original_c = ip_info.get("c", "")  # http模式失败原因
        original_d = ip_info.get("d", "")  # http模式页面1延迟
        original_h = ip_info.get("h", "")  # http模式页面2延迟
        original_e = ip_info.get("e", "")  # socks5模式 "成功次数,失败次数"
        original_f = ip_info.get("f", "")  # socks5模式失败原因
        original_g = ip_info.get("g", "")  # socks5模式页面1延迟
        original_i = ip_info.get("i", "")  # socks5模式页面2延迟
        
        # 解析成功和失败次数
        http_success = 0
        http_fail = 0
        if original_b:
            parts = original_b.split(",")
            if len(parts) == 2:
                try:
                    http_success = int(parts[0])
                    http_fail = int(parts[1])
                except:
                    pass
        
        socks5_success = 0
        socks5_fail = 0
        if original_e:
            parts = original_e.split(",")
            if len(parts) == 2:
                try:
                    socks5_success = int(parts[0])
                    socks5_fail = int(parts[1])
                except:
                    pass
        
        # 获取端口字段
        http_port = ip_info.get("port")
        socks5_port = ip_info.get("socketPort")
        
        # 检查HTTP端口
        http_port_valid = http_port is not None and str(http_port).strip() != ""
        if not http_port_valid:
            log_print(f"{log_prefix} ⚠ HTTP端口字段(port)不存在或为空，跳过HTTP测试，直接判定失败")
            http_result = {
                "success": False,
                "failure_reason": "0",  # 端口缺失
                "delay1": -1,
                "delay2": -1
            }
            http_fail += 1
            http_failure_reason = "0"
        else:
            # HTTP模式处理
            http_port_int = int(http_port) if isinstance(http_port, (int, str)) and str(http_port).strip() else None
            if http_port_int is None:
                log_print(f"{log_prefix} ⚠ HTTP端口字段(port)无效，跳过HTTP测试，直接判定失败")
                http_result = {
                    "success": False,
                    "failure_reason": "0",  # 端口无效
                    "delay1": -1,
                    "delay2": -1
                }
                http_fail += 1
                http_failure_reason = "0"
            else:
                http_result = process_ip_with_mode(ip_info, "http", http_port_int, browser_id, serial_number, log_prefix)
                
                # 记录HTTP模式结果
                if http_result["success"]:
                    http_success += 1
                    http_failure_reason = "1"  # HTTP成功记为1
                    log_print(f"{log_prefix} ✓ HTTP模式成功")
                else:
                    http_fail += 1
                    http_failure_reason = http_result.get("failure_reason", "0")
                    log_print(f"{log_prefix} ✗ HTTP模式失败: {http_failure_reason}")
        
        # 关闭浏览器，准备切换到socks5模式
        log_print(f"{log_prefix} 关闭浏览器，准备切换到socks5模式...")
        close_adspower_browser(serial_number)
        
        # 检查Socks5端口
        socks5_port_valid = socks5_port is not None and str(socks5_port).strip() != ""
        if not socks5_port_valid:
            log_print(f"{log_prefix} ⚠ Socks5端口字段(socketPort)不存在或为空，跳过Socks5测试，直接判定失败")
            socks5_result = {
                "success": False,
                "failure_reason": "0",  # 端口缺失
                "delay1": -1,
                "delay2": -1
            }
            socks5_fail += 1
            socks5_failure_reason = "0"
        else:
            # Socks5模式处理（无论HTTP是否成功，都要执行）
            socks5_port_int = int(socks5_port) if isinstance(socks5_port, (int, str)) and str(socks5_port).strip() else None
            if socks5_port_int is None:
                log_print(f"{log_prefix} ⚠ Socks5端口字段(socketPort)无效，跳过Socks5测试，直接判定失败")
                socks5_result = {
                    "success": False,
                    "failure_reason": "0",  # 端口无效
                    "delay1": -1,
                    "delay2": -1
                }
                socks5_fail += 1
                socks5_failure_reason = "0"
            else:
                socks5_result = process_ip_with_mode(ip_info, "socks5", socks5_port_int, browser_id, serial_number, log_prefix)
                
                # 记录Socks5模式结果
                if socks5_result["success"]:
                    socks5_success += 1
                    socks5_failure_reason = "1"  # Socks5成功记为1
                    log_print(f"{log_prefix} ✓ Socks5模式成功")
                else:
                    socks5_fail += 1
                    socks5_failure_reason = socks5_result.get("failure_reason", "0")
                    log_print(f"{log_prefix} ✗ Socks5模式失败: {socks5_failure_reason}")
        
        # 统一处理两种模式的结果并上传
        result_data["a"] = int(time.time())
        result_data["b"] = f"{http_success},{http_fail}"
        result_data["c"] = http_failure_reason
        result_data["d"] = http_result.get('delay1', -1)  # HTTP页面1延迟
        result_data["h"] = http_result.get('delay2', -1)  # HTTP页面2延迟
        result_data["e"] = f"{socks5_success},{socks5_fail}"
        result_data["f"] = socks5_failure_reason
        result_data["g"] = socks5_result.get('delay1', -1)  # Socks5页面1延迟
        result_data["i"] = socks5_result.get('delay2', -1)  # Socks5页面2延迟
        
        log_print(f"{log_prefix} [调试] 准备上传数据 - HTTP: delay1={result_data.get('d')}, delay2={result_data.get('h')}, success={http_result['success']}")
        log_print(f"{log_prefix} [调试] 准备上传数据 - Socks5: delay1={result_data.get('g')}, delay2={result_data.get('i')}, success={socks5_result['success']}")
        
        # 上传结果
        update_ip_info(result_data)
        log_print(f"{log_prefix} ✓ 任务完成，HTTP和Socks5两种模式结果已上传")
    except Exception as e:
        # 发生异常时，也要上传失败结果
        log_print(f"{log_prefix} ✗ 处理IP时发生异常: {str(e)}")
        import traceback
        log_print(f"{log_prefix} 异常详情:\n{traceback.format_exc()}")
        
        # 尝试上传异常结果
        try:
            result_data = ip_info.copy()
            result_data["a"] = int(time.time())
            # 如果已经有部分结果，保留；否则设置为失败
            if "b" not in result_data or not result_data.get("b"):
                result_data["b"] = "0,1"
            if "c" not in result_data or not result_data.get("c"):
                result_data["c"] = "0"
            if "d" not in result_data or result_data.get("d") is None:
                result_data["d"] = -1  # HTTP页面1延迟
            if "h" not in result_data or result_data.get("h") is None:
                result_data["h"] = -1  # HTTP页面2延迟
            if "g" not in result_data or result_data.get("g") is None:
                result_data["g"] = -1  # Socks5页面1延迟
            if "i" not in result_data or result_data.get("i") is None:
                result_data["i"] = -1  # Socks5页面2延迟
            update_ip_info(result_data)
            log_print(f"{log_prefix} ✓ 异常结果已上传")
        except Exception as upload_error:
            log_print(f"{log_prefix} ✗ 上传异常结果失败: {str(upload_error)}")
    finally:
        # 处理完成后，继续处理队列中的下一个IP
        pass


def process_ip_with_mode(ip_info, proxy_type, proxy_port, browser_id, serial_number, log_prefix):
    """
    使用指定代理模式处理IP
    
    Args:
        ip_info: IP信息字典
        proxy_type: 代理类型 ("http" 或 "socks5")
        proxy_port: 代理端口
        browser_id: 浏览器ID
        serial_number: 浏览器序列号
        log_prefix: 日志前缀，格式为 [浏览器id-ip]
        
    Returns:
        dict: 处理结果
            {
                "success": bool,
                "failure_reason": str,  # 失败原因
                "delay1": int,  # 页面1延迟（毫秒），失败为-1
                "delay2": int   # 页面2延迟（毫秒），失败为-1
            }
    """
    log_print(f"{log_prefix} [{proxy_type.upper()}] 开始使用{proxy_type}模式处理...")
    
    result = {
        "success": False,
        "failure_reason": "0",  # 0表示网络不通
        "delay1": -1,
        "delay2": -1
    }
    
    driver = None
    
    try:
        # 步骤1: 更新代理（重试3次）
        proxy_config = {
            "ip": ip_info["ip"],
            "port": proxy_port,
            "username": ip_info["username"],
            "password": ip_info["password"],
            "type": proxy_type,
            "isMain": ip_info.get("isMain", 0)
        }
        
        proxy_update_success = False
        for proxy_retry in range(1, 4):  # 重试3次
            try:
                if proxy_retry > 1:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤1: 更新代理 (重试第 {proxy_retry}/3 次)...")
                    time.sleep(2)  # 重试前等待2秒
                else:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤1: 更新代理...")
                
                if update_adspower_proxy(browser_id, proxy_config):
                    proxy_update_success = True
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✓ 更新代理成功")
                    break
                else:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 更新代理失败 (第 {proxy_retry}/3 次)")
                    if proxy_retry < 3:
                        continue
                    else:
                        result["failure_reason"] = "3"
                        return result
            except Exception as e:
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤1异常 (第 {proxy_retry}/3 次): {str(e)}")
                if proxy_retry < 3:
                    import traceback
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
                    time.sleep(2)  # 重试前等待2秒
                    continue
                else:
                    import traceback
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
                    result["failure_reason"] = "3"
                    return result
        
        if not proxy_update_success:
            result["failure_reason"] = "3"
            return result
        
        # 步骤2: 启动浏览器（重试3次）
        driver = None
        browser_start_success = False
        for browser_retry in range(1, 4):  # 重试3次
            try:
                if browser_retry > 1:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤2: 启动浏览器 (重试第 {browser_retry}/3 次)...")
                    time.sleep(2)  # 重试前等待2秒
                else:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤2: 启动浏览器...")
                
                browser_data = start_adspower_browser(serial_number)
                if not browser_data:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 启动浏览器失败 (第 {browser_retry}/3 次)")
                    if browser_retry < 3:
                        continue
                    else:
                        result["failure_reason"] = "3"
                        return result
                
                driver = create_selenium_driver(browser_data)
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✓ 浏览器启动成功")
                browser_start_success = True
                time.sleep(10)
                break
            except Exception as e:
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤2异常 (第 {browser_retry}/3 次): {str(e)}")
                if browser_retry < 3:
                    import traceback
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
                    # 清理可能已创建的driver
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = None
                    # 尝试关闭可能已启动的浏览器
                    try:
                        close_adspower_browser(serial_number)
                    except:
                        pass
                    time.sleep(2)  # 重试前等待2秒
                    continue
                else:
                    import traceback
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
                    result["failure_reason"] = "3"
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    close_adspower_browser(serial_number)
                    return result
        
        if not browser_start_success:
            result["failure_reason"] = "3"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        
        time.sleep(10)
        # 步骤3: 打开macro页面并记录延迟
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤3: 打开macro页面...")
            macro_url = "https://app.opinion.trade/macro"
            macro_delay = -1
            macro_success = False
            
            for macro_retry in range(1, 2):
                try:
                    if macro_retry > 1:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] 尝试刷新macro页面 (第 {macro_retry}/{MAX_RETRIES} 次)...")
                        time.sleep(5)  # 刷新前等待5秒
                    
                    macro_start_time = time.time()
                    driver.get(macro_url)
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✓ macro页面加载成功")
                    
                    # 等待页面加载完成：在60s内找到tbody元素，找到第一个tr，找到第一个td，等待td下出现p标签且内容不为空
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 等待macro页面加载完成...")
                    macro_load_success = False
                    timeout = 60
                    start_wait_time = time.time()
                    
                    while time.time() - start_wait_time < timeout:
                        try:
                            # 查找tbody元素
                            tbody_elements = driver.find_elements(By.TAG_NAME, "tbody")
                            if tbody_elements:
                                tbody = tbody_elements[0]
                                # 查找第一个tr
                                tr_elements = tbody.find_elements(By.TAG_NAME, "tr")
                                if tr_elements:
                                    first_tr = tr_elements[0]
                                    # 查找第一个td
                                    td_elements = first_tr.find_elements(By.TAG_NAME, "td")
                                    if td_elements:
                                        first_td = td_elements[0]
                                        # 查找p标签
                                        p_elements = first_td.find_elements(By.TAG_NAME, "p")
                                        if p_elements:
                                            p_text = p_elements[0].text.strip()
                                            if p_text != "":
                                                # 加载完成
                                                macro_delay = int((time.time() - macro_start_time) * 1000)  # 转换为毫秒
                                                log_print(f"{log_prefix} [{proxy_type.upper()}] ✓ macro页面加载完成，延迟: {macro_delay}ms")
                                                macro_success = True
                                                macro_load_success = True
                                                result["delay1"] = macro_delay
                                                break
                            time.sleep(0.5)  # 每0.5秒检查一次
                        except Exception as e:
                            time.sleep(0.5)
                            continue
                    
                    if macro_load_success:
                        break
                    else:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ macro页面加载未完成")
                        if macro_retry < MAX_RETRIES:
                            driver.refresh()
                            time.sleep(2)
                            continue
                        else:
                            result["delay1"] = -1
                            result["failure_reason"] = "4"
                            
                except (WebDriverException, TimeoutException) as e:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 打开macro页面失败 (第 {macro_retry}/{MAX_RETRIES} 次): {str(e)}")
                    if macro_retry < MAX_RETRIES:
                        time.sleep(5)
                        continue
                    else:
                        result["delay1"] = -1
                        result["failure_reason"] = "4"
        
            if not macro_success:
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ macro页面打开失败")
                result["delay1"] = -1
                result["failure_reason"] = "4"
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤3异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["delay1"] = -1
            result["failure_reason"] = "4"
         
        
        # 步骤4: 打开目标页面1（不再记录延迟）
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤4: 打开目标页面1...")
            target_url_1 = TARGET_URL_1
            page1_success = False
            
            for page_retry in range(1, MAX_RETRIES + 1):
                try:
                    if page_retry > 1:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] 尝试刷新页面 (第 {page_retry}/{MAX_RETRIES} 次)...")
                        time.sleep(5)  # 刷新前等待5秒
                    
                    driver.get(target_url_1)
                    page_load_success = True
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✓ 页面加载成功")
                    
                    # 等待页面完全加载
                    time.sleep(2)
                    
                    # 步骤5: 检查"I Understand and Agree"
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤5: 检查'I Understand and Agree'...")
                    if check_and_click_understand_agree(driver, browser_id, timeout=5):
                        log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 检测到'I Understand and Agree'，失败")
                        result["failure_reason"] = "2"
                        close_adspower_browser(serial_number)
                        return result
                    
                    # 步骤6: 等待页面真正完成加载
                    log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤6: 等待页面真正完成加载...")
                    trade_box = wait_for_opinion_trade_box(driver, serial_number, max_retries=3)
                    
                    if trade_box:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] ✓ 页面1加载完成")
                        page1_success = True
                        break
                    else:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 页面1加载未真正完成")
                        if page_retry < MAX_RETRIES:
                            refresh_page_with_opinion_check(driver, serial_number)
                            time.sleep(2)
                            continue
                        else:
                            result["failure_reason"] = "5"
                            close_adspower_browser(serial_number)
                            return result
                            
                except (WebDriverException, TimeoutException) as e:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 打开页面失败 (第 {page_retry}/{MAX_RETRIES} 次): {str(e)}")
                    if page_retry < MAX_RETRIES:
                        time.sleep(5)
                        continue
                    else:
                        result["failure_reason"] = "5"
                        close_adspower_browser(serial_number)
                        return result
        
            if not page1_success:
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 页面1打开失败")
                result["failure_reason"] = "5"
                close_adspower_browser(serial_number)
                return result
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤4异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["failure_reason"] = "5"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        # 步骤7: 检查地区限制
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤7: 检查地区限制...")
            if check_region_restriction(driver, browser_id, timeout=3):
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 检测到地区限制")
                result["failure_reason"] = "2"
                close_adspower_browser(serial_number)
                return result
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤7异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["failure_reason"] = "2"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        # 步骤8: 预打开OKX页面并连接钱包
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤8: 预打开OKX页面并连接钱包...")
            preopen_okx_wallet(driver, serial_number)
            connect_wallet_if_needed(driver, browser_id)
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤8异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["failure_reason"] = "6"  # 钱包连接失败
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        # 步骤9: 检测API限制
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤9: 检测API限制...")
            if check_api_restriction(driver, browser_id, timeout=3):
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 检测到API限制")
                result["failure_reason"] = "2"
                close_adspower_browser(serial_number)
                return result
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤9异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["failure_reason"] = "2"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        # 步骤9.5: 检查钱包连接状态
        try:
            time.sleep(10)
            connect_wallet_button = None
            okx_wallet_p = None
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    # 查找 Connect Wallet 按钮
                    connect_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in connect_buttons:
                        if button.text.strip() == "Connect Wallet":
                            connect_wallet_button = button
                            log_print(f"[{browser_id}] ✓ 找到 Connect Wallet 按钮")
                            break
                    
                    # 查找 OKX Wallet 的 p 标签
                    if not connect_wallet_button:
                        p_tags = driver.find_elements(By.TAG_NAME, "p")
                        for p in p_tags:
                            if p.text.strip() == "OKX Wallet":
                                okx_wallet_p = p
                                log_print(f"[{browser_id}] ✓ 找到 OKX Wallet 选项")
                                break
                    
                    # 如果找到了其中一个，停止查找
                    if connect_wallet_button or okx_wallet_p:
                        break
                    
                    # 如果3秒后两个都没找到，认为已连接
                    if time.time() - start_time > 3:
                        log_print(f"[{browser_id}] ✓ 未找到 Connect Wallet 按钮和 OKX Wallet 选项，钱包已连接")
                        break
                    
                    time.sleep(0.5)
                except:
                    time.sleep(0.5)
            
            # 10秒后，检查结果
            if connect_wallet_button or okx_wallet_p:
                result["failure_reason"] = "6"
                close_adspower_browser(serial_number)
                return result
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤9.5异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["failure_reason"] = "6"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        # 步骤10: 等待Position按钮
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤10: 等待Position按钮...")
            if not wait_for_position_button_with_retry(driver, browser_id, max_retries=2):
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ Position按钮未出现")
                result["failure_reason"] = "7"
                close_adspower_browser(serial_number)
                return result
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤10异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["failure_reason"] = "7"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        # 步骤11: 提交订单
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤11: 提交订单...")
            trade_box = driver.find_element(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
            order_success, failure_reason = submit_opinion_order_simple(driver, trade_box, browser_id, serial_number)
            
            if not order_success:
                if failure_reason == "8":
                    # 重试一次（重新获取trade_box，因为页面可能已变化）
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 提交订单失败，重试一次...")
                    time.sleep(2)
                    # 重新获取trade_box
                    try:
                        trade_box = driver.find_element(By.CSS_SELECTOR, 'div[data-flag="trade-box"]')
                    except:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 重试时无法找到trade-box")
                        result["failure_reason"] = "8"
                        close_adspower_browser(serial_number)
                        return result
                    order_success, failure_reason = submit_opinion_order_simple(driver, trade_box, browser_id, serial_number)
                
                if not order_success:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 提交订单失败")
                    result["failure_reason"] = failure_reason or "8"
                    close_adspower_browser(serial_number)
                    return result
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤11异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["failure_reason"] = "8"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
        # 步骤12: 打开目标页面2并获取Balance Spot地址
        try:
            log_print(f"{log_prefix} [{proxy_type.upper()}] 步骤12: 打开目标页面2...")
            target_url_2 = TARGET_URL_2
            page2_success = False
            page2_delay = -1
            
            for page2_retry in range(1, MAX_RETRIES + 1):
                try:
                    if page2_retry > 1:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] 刷新页面2 (第 {page2_retry}/{MAX_RETRIES} 次)...")
                        time.sleep(2)
                    
                    # 重新记录开始时间（每次重试都要重新记录）
                    start_time2 = time.time()
                    driver.get(target_url_2)
                    time.sleep(2)
                    
                    # 等待页面加载完成
                    address, address_success = get_balance_spot_address(driver, browser_id, timeout=30)
                    
                    if address_success:
                        page2_delay = int((time.time() - start_time2) * 1000)  # 转换为毫秒
                        log_print(f"{log_prefix} [{proxy_type.upper()}] ✓ 页面2加载完成，延迟: {page2_delay}ms")
                        page2_success = True
                        result["delay2"] = page2_delay
                        break
                    else:
                        log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 获取Balance Spot地址失败")
                        if page2_retry < MAX_RETRIES:
                            refresh_page_with_opinion_check(driver, serial_number)
                            time.sleep(2)
                            continue
                        else:
                            result["delay2"] = -1
                            result["failure_reason"] = "11"
                            # 页面2失败，关闭浏览器并返回
                            close_adspower_browser(serial_number)
                            return result
                            
                except Exception as e:
                    log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 打开页面2失败 (第 {page2_retry}/{MAX_RETRIES} 次): {str(e)}")
                    if page2_retry < MAX_RETRIES:
                        time.sleep(2)
                        continue
                    else:
                        result["delay2"] = -1
                        result["failure_reason"] = "11"
                        # 页面2失败，关闭浏览器并返回
                        close_adspower_browser(serial_number)
                        return result
        
            # 所有步骤成功
            if page1_success and page2_success:
                result["success"] = True
                result["failure_reason"] = "1"  # 成功记为1
                # 确保 delay2 被正确设置（如果页面2成功但 delay2 未设置，使用 page2_delay）
                if result.get("delay2") == -1 and page2_delay != -1:
                    result["delay2"] = page2_delay
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✓✓✓ 所有步骤成功完成")
                log_print(f"{log_prefix} [{proxy_type.upper()}] [调试] 最终结果 - delay1={result.get('delay1')}, delay2={result.get('delay2')}, success={result.get('success')}")
            else:
                # 理论上不应该到达这里，因为页面2失败时已经return了
                if not page2_success:
                    result["failure_reason"] = "11"
                log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 部分步骤失败")
            
            # 关闭浏览器
            close_adspower_browser(serial_number)
        except Exception as e:
            log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 步骤12异常: {str(e)}")
            import traceback
            log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
            result["delay2"] = -1
            result["failure_reason"] = "11"
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            close_adspower_browser(serial_number)
            return result
        
    except Exception as e:
        # 这是最后的兜底异常处理，理论上不应该到达这里
        log_print(f"{log_prefix} [{proxy_type.upper()}] ✗ 处理过程中发生未捕获的异常: {str(e)}")
        import traceback
        log_print(f"{log_prefix} [{proxy_type.upper()}] 异常详情:\n{traceback.format_exc()}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        close_adspower_browser(serial_number)
    
    return result


# ============================================================================
# 主函数
# ============================================================================

def main():
    """
    主函数 - 循环获取任务并处理
    """
    log_print("="*80)
    log_print("IP测试脚本启动")
    log_print("="*80)
    
    # 主循环：每隔5秒请求一次任务
    while True:
        try:
            # 获取任务
            mission = get_mission_from_server()
            
            if mission and mission.get("id"):
                mission_id = mission.get("id")
                log_print(f"[系统] 获取到任务 ID: {mission_id}，开始处理...")
                
                # 判断 numberList 是否为空或 null
                number_list = mission.get("numberList")
                if number_list and number_list.strip():
                    # numberList 有值，处理单个任务
                    log_print(f"[系统] 检测到 numberList 有值: {number_list}，执行单个任务模式")
                    
                    browser_id = number_list.strip()
                    tp1 = mission.get("tp1")
                    if not tp1 or not tp1.strip():
                        log_print(f"[系统] ✗ tp1 字段为空，无法执行任务")
                        submit_mission_result(
                            mission_id=mission_id,
                            success_count=0,
                            failed_count=0,
                            failed_info={},
                            status=3,  # 失败
                            custom_msg="tp1字段为空"
                        )
                        log_print(f"[系统] 等待5秒后继续获取下一个任务...")
                        time.sleep(5)
                        continue
                    
                    ip = tp1.strip()
                    log_print(f"[系统] 单个任务 - 浏览器ID: {browser_id}, IP: {ip}")
                    
                    # 尝试从 get_all_ip_info 中查找对应的 IP 信息，以获取完整的配置
                    ip_list, success = get_all_ip_info()
                    ip_info = None
                    
                    if success and ip_list:
                        # 查找对应的 IP 信息（将number转换为字符串进行比较）
                        for item in ip_list:
                            item_number = str(item.get("number", "")).strip()
                            item_ip = str(item.get("ip", "")).strip()
                            if item_number == browser_id and item_ip == ip:
                                ip_info = item.copy()
                                log_print(f"[系统] ✓ 找到对应的IP配置信息")
                                break
                    
                    # 如果没有找到，使用默认配置构造 ip_info
                    if not ip_info:
                        log_print(f"[系统] ⚠ 未找到对应的IP配置，使用默认配置")
                        ip_info = {
                            "ip": ip,
                            "number": browser_id,
                            "username": "nolanwang",  # 默认用户名
                            "password": "HFVsyegfeyigrfkjb",  # 默认密码
                            "isMain": 0
                        }
                    
                    # 启动处理任务（异步，不等待完成）
                    try:
                        log_print(f"[系统] 开始处理单个任务: 浏览器ID={browser_id}, IP={ip}")
                        
                        # 确保全局线程池已初始化
                        init_global_thread_pool()
                        
                        # 使用线程池异步处理，不阻塞主循环
                        def process_single_task():
                            try:
                                process_ip(ip_info)
                            except Exception as e:
                                log_print(f"[系统] ✗ 处理单个任务异常: {str(e)}")
                                import traceback
                                log_print(f"[系统] 异常详情:\n{traceback.format_exc()}")
                        
                        # 使用全局线程池提交任务，确保不超过最大线程数
                        with GLOBAL_THREAD_POOL_LOCK:
                            if GLOBAL_THREAD_POOL is not None:
                                GLOBAL_THREAD_POOL.submit(process_single_task)
                                log_print(f"[系统] ✓ 单个任务已提交到线程池（当前线程池大小: {THREAD_COUNT}）")
                            else:
                                # 如果线程池未初始化，回退到直接创建线程（不应该发生）
                                log_print(f"[系统] ⚠ 全局线程池未初始化，使用直接线程创建")
                                task_thread = threading.Thread(target=process_single_task, daemon=True)
                                task_thread.start()
                        
                        # 只要开始运行了，就返回任务成功
                        log_print(f"[系统] ✓ 单个任务已开始处理，保存任务为成功")
                        submit_mission_result(
                            mission_id=mission_id,
                            success_count=1,
                            failed_count=0,
                            failed_info={},
                            status=2  # 成功
                        )
                    except Exception as e:
                        log_print(f"[系统] ✗ 启动单个任务处理失败: {str(e)}")
                        submit_mission_result(
                            mission_id=mission_id,
                            success_count=0,
                            failed_count=1,
                            failed_info={browser_id: f"启动失败: {str(e)}"},
                            status=3  # 失败
                        )
                    
                    log_print(f"[系统] 等待5秒后继续获取下一个任务...")
                    time.sleep(5)
                    continue
                
                # numberList 为空或 null，执行原有逻辑：获取所有IP列表
                log_print(f"[系统] numberList 为空或 null，执行批量任务模式")
                
                # 获取IP列表（带重试机制）
                ip_list, success = get_all_ip_info()
                
                if not success:
                    # 3次都失败了，保存任务为失败
                    log_print(f"[系统] ✗ 获取IP列表失败，保存任务 {mission_id} 为失败")
                    submit_mission_result(
                        mission_id=mission_id,
                        success_count=0,
                        failed_count=0,
                        failed_info={},
                        status=3,  # 失败
                        custom_msg="服务器数据列表获取失败"
                    )
                    log_print(f"[系统] 等待5秒后继续获取下一个任务...")
                    time.sleep(5)
                    continue
                
                if not ip_list:
                    log_print(f"[系统] ✗ 获取到空的IP列表，保存任务 {mission_id} 为失败")
                    submit_mission_result(
                        mission_id=mission_id,
                        success_count=0,
                        failed_count=0,
                        failed_info={},
                        status=3,  # 失败
                        custom_msg="服务器数据列表获取失败"
                    )
                    log_print(f"[系统] 等待5秒后继续获取下一个任务...")
                    time.sleep(5)
                    continue
                
                log_print(f"[系统] ✓ 获取到 {len(ip_list)} 个IP，开始使用 {THREAD_COUNT} 个线程处理...")
                log_print(f"[系统] 调度策略: 第一批任务间隔5秒启动，之后任务完成时立即调度新任务")
                
                # 待处理任务队列
                pending_tasks = ip_list.copy()
                pending_tasks_lock = threading.Lock()
                
                # 正在运行的浏览器ID集合
                running_browser_ids = set()
                running_browser_ids_lock = threading.Lock()
                
                # 已完成任务计数
                completed_count = 0
                completed_count_lock = threading.Lock()
                
                # 成功和失败计数
                success_count = 0
                failed_count = 0
                failed_info = {}
                
                def get_next_available_task():
                    """获取下一个可执行的任务（跳过浏览器ID正在运行的任务）"""
                    with pending_tasks_lock:
                        if not pending_tasks:
                            return None
                        
                        # 查找第一个浏览器ID不在运行中的任务
                        # 同时检查BROWSER_PROCESSING，因为process_ip内部也会管理队列
                        for i, ip_info in enumerate(pending_tasks):
                            browser_id = ip_info.get("number", "unknown")
                            with running_browser_ids_lock:
                                # 检查是否在主调度器的运行列表中
                                if browser_id in running_browser_ids:
                                    continue
                            # 检查是否在process_ip的内部处理列表中
                            with BROWSER_PROCESSING_LOCK:
                                if browser_id in BROWSER_PROCESSING and BROWSER_PROCESSING[browser_id]:
                                    continue
                            
                            # 找到可用任务，移除并标记浏览器ID为运行中
                            task = pending_tasks.pop(i)
                            with running_browser_ids_lock:
                                running_browser_ids.add(browser_id)
                            return task
                        
                        # 所有待处理任务的浏览器ID都在运行中，返回None
                        return None
                
                def task_completed(browser_id, task_success=True, failure_reason=None):
                    """任务完成回调"""
                    with running_browser_ids_lock:
                        running_browser_ids.discard(browser_id)
                    with completed_count_lock:
                        nonlocal completed_count, success_count, failed_count
                        completed_count += 1
                        if task_success:
                            success_count += 1
                        else:
                            failed_count += 1
                            if browser_id:
                                failed_info[browser_id] = failure_reason or ""
                
                def worker():
                    """工作线程函数 - 持续获取并处理任务"""
                    while True:
                        # 获取下一个可用任务
                        task = get_next_available_task()
                        
                        if task is None:
                            # 没有可用任务
                            with pending_tasks_lock:
                                if not pending_tasks:
                                    # 没有待处理任务了，退出
                                    break
                                else:
                                    # 还有待处理任务，但浏览器ID都在运行，等待一下再重试
                                    time.sleep(0.5)
                                    continue
                        
                        browser_id = task.get("number", "unknown")
                        ip = task.get("ip", "unknown")
                        log_print(f"[系统] 开始处理任务: IP={ip}, 浏览器ID={browser_id}")
                        
                        task_success = True
                        failure_reason = None
                        try:
                            # 处理任务（process_ip不返回值，成功或失败由内部逻辑处理并上传）
                            process_ip(task)
                            # 如果没有抛出异常，认为任务已处理完成
                        except Exception as e:
                            log_print(f"[系统] ✗ 处理任务异常: {str(e)}")
                            import traceback
                            log_print(f"[系统] 异常详情:\n{traceback.format_exc()}")
                            task_success = False
                            failure_reason = f"异常: {str(e)}"
                        finally:
                            # 任务完成，释放浏览器ID
                            task_completed(browser_id, task_success, failure_reason)
                            with completed_count_lock:
                                log_print(f"[系统] 任务完成: IP={ip}, 浏览器ID={browser_id} (已完成: {completed_count}/{len(ip_list)})")
                
                # 使用线程池
                with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                    # 第一批任务：间隔5秒启动worker线程
                    worker_futures = []
                    initial_count = min(THREAD_COUNT, len(ip_list))
                    
                    log_print(f"[系统] 第一批启动 {initial_count} 个worker线程，间隔5秒...")
                    for i in range(initial_count):
                        if i > 0:
                            log_print(f"[系统] 等待5秒后启动第 {i + 1} 个worker线程...")
                            time.sleep(5)
                        
                        log_print(f"[系统] 启动worker线程 {i + 1}/{initial_count}")
                        future = executor.submit(worker)
                        worker_futures.append(future)
                    
                    log_print(f"[系统] 所有worker线程已启动，开始动态调度任务...")
                    
                    # 等待所有worker线程完成
                    for i, future in enumerate(worker_futures):
                        try:
                            future.result()
                            log_print(f"[系统] Worker线程 {i + 1} 已完成")
                        except Exception as e:
                            log_print(f"[系统] ✗ Worker线程 {i + 1} 异常: {str(e)}")
                            import traceback
                            log_print(f"[系统] 异常详情:\n{traceback.format_exc()}")
                
                log_print("="*80)
                log_print(f"任务 {mission_id} 处理完成 (总计: {completed_count}/{len(ip_list)}, 成功: {success_count}, 失败: {failed_count})")
                log_print("="*80)
                
                # 保存任务结果
                submit_mission_result(
                    mission_id=mission_id,
                    success_count=success_count,
                    failed_count=failed_count,
                    failed_info=failed_info,
                    status=2  # 成功
                )
                
            else:
                # 没有获取到任务，等待5秒后继续
                log_print(f"[系统] 未获取到任务，等待5秒后继续...")
                time.sleep(5)
                
        except KeyboardInterrupt:
            log_print("\n[系统] 收到中断信号，程序退出")
            break
        except Exception as e:
            log_print(f"[系统] ✗ 主循环异常: {str(e)}")
            import traceback
            log_print(f"[系统] 异常详情:\n{traceback.format_exc()}")
            log_print(f"[系统] 等待5秒后继续...")
            time.sleep(5)


def init_global_thread_pool():
    """初始化全局线程池"""
    global GLOBAL_THREAD_POOL
    with GLOBAL_THREAD_POOL_LOCK:
        if GLOBAL_THREAD_POOL is None:
            GLOBAL_THREAD_POOL = ThreadPoolExecutor(max_workers=THREAD_COUNT)
            log_print(f"[系统] 全局线程池已初始化，最大线程数: {THREAD_COUNT}")


def shutdown_global_thread_pool():
    """关闭全局线程池"""
    global GLOBAL_THREAD_POOL
    with GLOBAL_THREAD_POOL_LOCK:
        if GLOBAL_THREAD_POOL is not None:
            log_print("[系统] 正在关闭全局线程池...")
            GLOBAL_THREAD_POOL.shutdown(wait=True)
            GLOBAL_THREAD_POOL = None
            log_print("[系统] 全局线程池已关闭")


if __name__ == "__main__":
    # 初始化并启动主循环
    initialize_fingerprint_mapping()
    init_global_thread_pool()
    try:
        main()
    finally:
        shutdown_global_thread_pool()
