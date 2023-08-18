#  ctext 繁简转换纠错辅助工具 

该工具会访问给定的 ctext.org 书籍、章节页面，分析其中每一个汉字的繁简转换情况，如果发现该繁体汉字所对应的简体汉字如果存在对应多个繁体汉字的可能性，则给出提示，以便编辑人员进行人工判断。

## 工具使用方法

目前工具已经部署在 streamlit 上，可以直接访问使用：

https://ctext-checker.streamlit.app/

## 本地部署

如果需要本地运行，可以下载本项目：

```bash
git clone https://github.com/twang2218/ctext-helper.git
```

然后安装依赖：

```bash
cd ctext-helper
pip install -r requirements.txt
```

运行可以分为网页模式和命令行模式。

### 网页模式

```bash
streamlit run ctext.py
```

### 命令行模式

```bash
python ctext.py --url="https://ctext.org/wiki.pl?if=gb&res=143901" --file=output.txt
```

> 如不加 `--file` 参数，将从命令行直接输出。
