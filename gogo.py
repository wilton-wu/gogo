#!/usr/bin/env python

import sys
from pathlib import Path
from os import environ

__version__ = "2.0.0"

HELP_MSG = """gogo - 快速目录导航工具

用法:
  gogo [选项] | [目录别名] | [目录别名/子目录/路径]

选项:
  -a, --add 别名   : 将当前目录以指定别名添加到配置中
  -l, --ls         : 列出所有已配置的别名及其对应路径
  -e, --edit       : 在$EDITOR中打开配置文件进行编辑
  -h, --help       : 显示此帮助信息
  -v, --version    : 显示版本信息并退出

示例:
  gogo              # 导航到默认目录(如未设置则为$HOME)
  gogo work         # 导航到别名为"work"的目录
  gogo work/src/lib # 导航到"work"别名目录下的子路径
  gogo -a proj      # 将当前目录添加为别名"proj"
  gogo -l           # 查看所有已配置的别名

SSH支持:
  gogo server       # 如果"server"配置为SSH别名，将连接到远程服务器

配置文件位于 ~/.config/gogo/gogo.conf
配置格式: 别名 = 路径 或 别名 = ssh://服务器信息:shell /路径"""

# 使用Path对象处理路径，更加安全和跨平台
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "gogo"
CONFIG_NAME = "gogo.conf"
CONFIG_PATH = CONFIG_DIR / CONFIG_NAME

DEFAULT_CONFIG = [
    "# 这是一个'gogo'配置文件示例\n",
    "# 每行以'#'字符开头的被视为注释。\n",
    "# 每个条目应该采用以下格式：\n",
    "# 目录别名 = /目录/路径/\n",
    "# 示例：\n",
    "\n",
    f"default = {HOME_DIR}\n",
    "\n",
    "# 'default'是一个特殊别名，当没有给gogo提供别名时使用。\n",
    "# 如果您没有在配置文件中指定它，它将指向您的主目录。\n",
    "\n",
    "# 您也可以连接到ssh服务器上的目录，但语法略有不同：\n",
    "# 目录别名 = ssh://服务器名称:选择的shell /目录/路径/\n\n",
    "# 如果您愿意，可以省略shell，但在这种情况下gogo将使用${SHELL}变量。\n",
    "# 目录别名 = ssh://第二个服务器 /目录/路径/\n",
    "\n",
    f"sshloc = ssh://{Path.home().name}@127.0.0.1:/bin/bash {HOME_DIR}\n",
    "- = -\ngogo = ~/.config/gogo\n",
]


def echo(text, output=sys.stdout, endline=True):
    """输出文本到指定输出流"""
    if output == sys.stdout:
        output.write(f"echo{' -n' if not endline else ''} '{text}';")
    else:
        output.write(f"{text}{chr(10) if endline else ''}")


def call(cmd):
    """执行命令并退出"""
    sys.stdout.write(f"{cmd};\n")
    sys.exit(0)


def printVersion():
    """打印版本信息并退出"""
    echo(f"gogo {__version__}")
    sys.exit(0)


def fatalError(msg, status=1):
    """打印错误信息并以指定状态码退出"""
    echo(msg, sys.stderr)
    sys.exit(status)


def _changeDirectory(directory):
    """切换到指定目录"""
    if directory.startswith("~/"):
        directory = str(HOME_DIR / directory[2:])
    call(f"cd '{directory}'")


def _sshToAddress(address):
    """SSH连接到远程地址"""
    try:
        addressPart, directory = address.split(" ", 1)
        splitted = addressPart.split(":")
        server = splitted[0]
        shell = splitted[1] if len(splitted) > 1 else "${SHELL}"

        call(f"ssh {server} -t 'cd {directory}; {shell}'")
    except ValueError:
        fatalError("SSH地址格式错误，正确格式为: ssh://server[:shell] /path")


def processRequest(request):
    """处理用户请求"""
    if request.startswith("ssh://"):
        address = request.replace("ssh://", "", 1)
        _sshToAddress(address)
    else:
        _changeDirectory(request)


def printConfig(config):
    """打印配置信息"""
    echo("当前gogo配置（按字母顺序排序）：")
    if config:
        justification = len(max(config.keys(), key=len)) + 2

        # 排序
        configList = sorted(config.items(), key=lambda x: x[0])

        for key, val in configList:
            keyStr = str(key)  # 直接转换为字符串，Python 3中默认是Unicode
            valStr = f" : {val}"
            echo(keyStr.rjust(justification), endline=False)
            echo(valStr)
    else:
        echo("  [ 没有配置 ] ", sys.stderr)


def createNonExistingConfigDir():
    """创建配置目录（如果不存在）"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def openConfigInEditor():
    """在编辑器中打开配置文件"""
    try:
        editor = environ["EDITOR"]
    except KeyError:
        echo("未设置$EDITOR。尝试使用vi。", sys.stderr)
        editor = "vi"
    call(f"{editor} {CONFIG_PATH}")
    sys.exit(1)


def readConfig():
    """读取配置文件内容"""
    createNonExistingConfigDir()
    try:
        with CONFIG_PATH.open("r") as file_:
            lines = file_.readlines()
    except IOError:
        lines = DEFAULT_CONFIG
        with CONFIG_PATH.open("w+") as file_:
            file_.writelines(lines)
    return lines


def prepareString(text, strip_chars="\"' "):
    """准备字符串，去除两端的指定字符"""
    return text.strip(strip_chars)


def parseConfig(lines):
    """解析配置文件内容"""
    configDict = {}
    for lineNo, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        try:
            key, value = line.split("=", 1)
            configDict[prepareString(key)] = prepareString(value)
        except ValueError:
            fatalError(f"错误地解析配置文件..\n  在第{lineNo + 1}行:\n  {line}")
    
    return configDict


def addAlias(alias, currentConfig):
    """添加新别名到配置文件"""
    if alias not in currentConfig:
        currentDir = Path.cwd()

        with CONFIG_PATH.open("a") as file_:
            file_.write(f"{alias} = {currentDir}\n")
    else:
        fatalError(f"别名'{alias}'已经存在！")


def parseAlias(alias, config):
    """解析用户输入的别名。返回一个元组：('dir', 'remainder_path')。
    这是因为用户可以输入类似"alias/child/directory"的内容，而gogo
    应该将目录更改为"dir/child/directory"。"""

    # 先检查完整别名是否存在
    if alias in config:
        return (config[alias], "")

    # 尝试拆分路径
    splitted = alias.split("/", 1)
    base_alias = splitted[0]
    
    if base_alias not in config:
        fatalError(f"在配置文件中找不到'{alias}'！")
        
    remainder = splitted[1] if len(splitted) > 1 else ""
    return (config[base_alias], remainder)


def main():
    """主函数"""
    lines = readConfig()
    args = sys.argv[1:]
    
    # 无参数情况：导航到默认目录
    if not args:
        config = parseConfig(lines)
        processRequest(config.get("default", str(HOME_DIR)))
        return
        
    # 单参数情况
    if len(args) == 1:
        arg = args[0]
        
        # 处理选项
        options = {
            ("-h", "--help"): lambda: echo(HELP_MSG),
            ("-v", "--version"): printVersion,
            ("-l", "--ls"): lambda: printConfig(parseConfig(lines)),
            ("-e", "--edit"): openConfigInEditor,
            ("-a", "--add"): lambda: fatalError("未指定要添加的别名！")
        }
        
        for option_keys, action in options.items():
            if arg in option_keys:
                action()
                return
        
        # 处理别名导航
        config = parseConfig(lines)
        newdir, remainder = parseAlias(arg, config)
        if remainder:  # 修复例如'gogo -'，它将导致'-/'
            processRequest(str(Path(newdir) / remainder))
        else:
            processRequest(newdir)
        return
            
    # 双参数情况
    if len(args) == 2 and args[0] in ("-a", "--add"):
        config = parseConfig(lines)
        addAlias(args[1], config)
        return
        
    # 其他情况：显示帮助
    fatalError(HELP_MSG, 2 if len(args) == 2 else 3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(2)
