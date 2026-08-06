FROM python:3.11-slim

WORKDIR /app

COPY agent-server/requirements.txt ./requirements.txt
COPY sdk ./sdk
RUN pip install --no-cache-dir -r requirements.txt ./sdk

COPY agent-server/support_agent ./support_agent
COPY agent-server/langgraph.json ./

EXPOSE 2024

CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser", "--no-reload"]
