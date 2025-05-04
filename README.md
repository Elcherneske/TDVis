## Hello There.\(@^0^@)/🎉
Here is TDvis, a streamlit app aims to provide a simple, simple and pretty simple vision into the PTMS of top-down proteomics data.(pre-analyzed by Toppic)

friendly for the people who are not specialist of Proteomics

Thanks:
- Toppic : Data procession
- Streamlit : Super Web construction
- plotly : Wonderful data sharing



## 🖱️ 一键式部署指南
为了便于分享,我们在release中提供了可以本地部署的安装包

>在空白的新工控机上试验通过,测试版本python3.13

1. 下载压缩包解压后双击运行 `init.bat`
2. 等待自动完成以下步骤：
   - ✅ 创建 Python 虚拟环境
   - ✅ 安装所有依赖库
   - ✅ 启动本地服务器
   - 大致需要三分钟
3. 在自动打开的浏览器界面中,输入你所要查看的文件的地址,即可开始查看
   1. 比如example文件夹中的示例文件,复制文件地址,然后直接输入文本框即可

>之后的启动,只需要运行 `start.bat` 即可

>如果您的电脑上没有python,在安装python的时候,请确保python被添加到了环境变量中.
>兼容3.13

## advanced

### 其他环境管理工具
- 默认使用uv进行虚拟环境的管理
- 如果您需要使用其他的虚拟环境管理工具,比如conda,必要的环境配置已经在requirements.txt中.您可以自行调用.

### 文件夹要求
- 在分析测试平台中与TDworkflow同步使用
- 该程序识别TDworkflow输出的文件夹,也就是_html文件的上级文件夹.
- 程序会自动解析文件夹中所包含的不同进样批次.

### 外观自定义
这一部分是streamlit插件自带的功能,在网页界面右上角可以进行查看
