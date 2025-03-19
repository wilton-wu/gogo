# GOGO

GOGO 是一款强大的目录书签工具，让你在命令行中轻松管理常用目录。有了它，你再也不用记忆那些又长又复杂的路径了。只需在任意位置输入 `gogo xmas`，就能立即跳转到 `~/Pictures/from_mum/1994/12/christmas` 这样的目录。更棒的是，你还可以用同样简单的方式连接到远程 SSH 服务器！

## 安装步骤

由于 shell 脚本的特性，GOGO 在子 shell 中执行时无法直接改变父 shell 的目录。因此，安装 GOGO 需要完成以下两个步骤：

1. 将 `gogo.py` 复制到你的环境变量 `$PATH` 包含的任意目录中，例如 ~/bin/：
   ```bash
   mkdir -p ~/bin && cp gogo.py ~/bin/
   ```

2. 将 `gogo.sh` 中的函数添加到你的 shell 配置文件中：

   对于 Bash 用户：
   ```bash
   cat gogo.sh >> ~/.bashrc
   ```
   
   对于 Zsh 用户：
   ```bash
   cat gogo.sh >> ~/.zshrc
   ```
   
   或者使用 source 方式（Bash 为例）：
   ```bash
   cp gogo.sh ~/.gogo.sh && echo "source ~/.gogo.sh" >> ~/.bashrc
   ```

   建议：你也可以使用你熟悉的文本编辑器手动完成上述操作，这通常是最安全的方式。

## 使用方法

```
gogo                 # 跳转到默认目录，如未设置则跳转到用户主目录($HOME)
gogo alias           # 跳转到名为'alias'的目录书签
gogo alias/child/dir # 跳转到书签目录下的子目录路径
gogo -a alias        # 将当前目录添加为新的书签
gogo -h, gogo --help # 显示帮助信息
gogo -l, gogo --ls   # 列出所有已配置的书签
gogo -e, gogo --edit # 在默认编辑器($EDITOR)中打开配置文件
```

**注意事项：**
- 如果你的书签名称中已包含斜杠，将无法使用子目录跳转功能
- GOGO 将所有用户输出打印到标准错误流(`stderr`)，这是实现其功能的必要方式，但可能导致在重定向输出时看不到提示信息

## 配置详解

GOGO 的配置文件位于 `~/.config/gogo/gogo.conf`，首次使用时会自动创建。配置语法非常简单：

```
# 注释是以 '#' 字符开头的行
default = ~/something          # 默认目录
work = /path/to/work           # 普通路径书签
documents = /path/with space   # 包含空格的路径
projects = "/this/also/works"  # 引号包裹的路径也有效
中文别名 = "/unicode/支持/中文路径"  # 完全支持Unicode和中文
```

**特别说明：**
- `default` 是特殊书签，当不带参数执行 `gogo` 时会跳转到此目录
- 如果配置文件中未设置 `default`，则默认使用用户主目录(`$HOME`)
- 注释必须单独成行，不能与书签定义放在同一行

### SSH远程连接

GOGO 还支持为SSH远程目录创建书签：

```
remote_work = ssh://username@server:bash /remote/path
cloud_server = ssh://server_alias ~/projects
```

格式说明：
- `server_info` 部分使用标准SSH格式，可以是 `用户名@服务器` 或 `~/.ssh/config` 中定义的主机别名
- 冒号后的 `shell` 参数是可选的，指定登录后使用的shell（若未指定则使用 `$SHELL` 环境变量的值）
- 空格后是登录成功后要切换到的远程路径

## 调试技巧

如果你想了解 GOGO 执行了哪些具体命令，可以直接调用 Python 脚本：

```bash
~/bin/gogo.py
```
