# 使用与调试指南（中文）

这份指南带你在自己的电脑上把项目跑起来，然后学会在三个地方调试：Python 模型服务、Java 后端、浏览器网页。

## 1. 安装工具（只需一次）

| 工具 | 用途 | 下载 |
| --- | --- | --- |
| Git | 下载和提交代码 | https://git-scm.com/downloads |
| Python 3.10 或更新 | 运行模型服务 | https://www.python.org/downloads/ （Windows 安装时勾选 "Add python.exe to PATH"） |
| JDK 17 或更新 | 运行 Java 后端 | https://adoptium.net/ |
| IntelliJ IDEA | 写和调试 Java（自带 Maven） | https://www.jetbrains.com/idea/ （学生用学校邮箱可免费用 Ultimate） |
| VS Code 或 PyCharm | 写和调试 Python | https://code.visualstudio.com/ （装 Python 插件） |

装好后在终端（Windows 用 PowerShell，Mac 用 Terminal）检查：

```bash
git --version
python --version     # Mac 上可能是 python3 --version
java -version
```

## 2. 下载代码

```bash
git clone https://github.com/wuzetao46-sys/credit-risk-scoring.git
cd credit-risk-scoring
```

## 3. 启动 Python 模型服务（终端 1）

```bash
cd ml-service
python -m venv .venv                 # 建一个只属于本项目的 Python 环境
.venv\Scripts\activate               # Windows
source .venv/bin/activate            # Mac / Linux
pip install -r requirements.txt      # 安装依赖，第一次要几分钟
python download_data.py              # 下载数据集到 data/
python train.py                      # 训练模型，会打印 AUC 等结果
python -m pytest                     # 跑测试，应显示 4 passed
uvicorn app:app --port 8000          # 启动服务，这个窗口不要关
```

打开 http://localhost:8000/docs ，点 `POST /predict` → **Try it out**，把下面这段贴进去点 **Execute**，就能直接看到模型的返回：

```json
{"LIMIT_BAL": 20000, "EDUCATION": 2, "MARRIAGE": 2, "AGE": 24,
 "PAY_0": 3, "PAY_2": 2, "PAY_3": 2, "PAY_4": 2, "PAY_5": 2, "PAY_6": 2,
 "BILL_AMT1": 19000, "BILL_AMT2": 18500, "BILL_AMT3": 18000, "BILL_AMT4": 17000, "BILL_AMT5": 16500, "BILL_AMT6": 16000,
 "PAY_AMT1": 0, "PAY_AMT2": 0, "PAY_AMT3": 0, "PAY_AMT4": 500, "PAY_AMT5": 500, "PAY_AMT6": 500}
```

## 4. 启动 Java 后端（IntelliJ）

1. IntelliJ → **Open** → 选 `backend` 文件夹（里面有 pom.xml），等右下角 Maven 下载依赖完成。
2. 打开 `src/main/java/uk/ac/surrey/creditrisk/CreditRiskApplication.java`，点 `main` 方法左边的绿色三角 → **Run**。
3. 控制台出现 `Started CreditRiskApplication` 就成功了。
4. 浏览器打开 http://localhost:8080 ，点 **Late payer** 再点 **Score applicant**。

不用 IntelliJ 也可以在终端 2 里运行 `cd backend` 然后 `mvn spring-boot:run`。

## 5. 调试

### 5.1 Java 后端：断点

1. 打开 `controller/ApplicationController.java`，在 `score` 方法里 `Prediction prediction = modelClient.predict(...)` 这一行的行号左边点一下，出现红点。
2. 停掉之前的运行，改点绿色小虫子图标 **Debug**。
3. 在网页上提交一个申请，IntelliJ 会停在这一行。
4. 下方 **Debugger** 面板能看到 `request` 里的每个字段；按 **F8** 执行下一行，然后看 `prediction` 的值。
5. 按 **F9** 继续运行。

### 5.2 Python 模型服务：断点

最简单的方法：在 `app.py` 的 `predict` 函数里加一行 `breakpoint()`，保存后重启 uvicorn。再提交一次申请，终端 1 会停下进入调试器：

- 输入 `p probability` 查看变量
- 输入 `n` 执行下一行，`c` 继续运行
- 调试完记得删掉 `breakpoint()`

用 VS Code 的话：打开 `ml-service` 文件夹，在行号左边点红点，按 **F5** → 选 **Python Debugger** → **FastAPI**，它会用调试模式启动 uvicorn。

### 5.3 网页：浏览器开发者工具

在 http://localhost:8080 按 **F12**（Mac：Cmd+Option+I）：

- **Network**：提交申请后点 `applications` 这一条，能看到发给后端的 JSON（Payload）和返回的结果（Response）。
- **Console**：JavaScript 报错会显示在这里。也可以在 `app.js` 里写 `console.log(变量)` 打印。
- **Sources**：打开 `app.js`，可以像 IntelliJ 一样点行号打断点。

### 5.4 数据库：用 SQL 查看记录

打开 http://localhost:8080/h2-console ，JDBC URL 填 `jdbc:h2:file:./data/creditrisk`，用户 `sa`，密码留空，点 Connect，然后运行：

```sql
SELECT applicant_name, probability_of_default, decision, created_at
FROM loan_application
ORDER BY created_at DESC;
```

## 6. 常见问题

| 现象 | 原因和解决 |
| --- | --- |
| 网页上 "Model service not reachable" | 终端 1 的 uvicorn 没在运行，重新执行第 3 步最后一行 |
| `ModuleNotFoundError: No module named 'xgboost'` | 没激活虚拟环境，先运行 activate 那一行 |
| `Port 8080 was already in use` | 后端已经开着一个，先停掉旧的（IntelliJ 点红色方块） |
| `python download_data.py` 下载失败 | 网络问题，重试；或手动从 UCI 网站下载 .xls 放到 `ml-service/data/default_of_credit_card_clients.xls` |
| Mac 上 xgboost 报 `libomp` 错误 | 运行 `brew install libomp` |
| IntelliJ 里代码一片红 | 右键 pom.xml → **Maven** → **Reload project** |

## 7. 改完代码后提交到 GitHub

```bash
git status                      # 看改了哪些文件
git add .
git commit -m "描述你改了什么"
git push
```
