FROM ubuntu:22.04

WORKDIR /app
COPY . .

RUN apt update && apt install cmake g++ -y && make && chmod +x ./magazinchik
CMD ["./magazinchik"]
