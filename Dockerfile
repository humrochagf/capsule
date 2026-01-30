FROM astral/uv:python3.13-alpine

ENV UV_COMPILE_BYTECODE=1

COPY . /app

WORKDIR /app

RUN uv sync --no-dev

EXPOSE 9292

ENTRYPOINT ["uv", "run", "--no-sync", "capsule"]

CMD ["start-server"]
