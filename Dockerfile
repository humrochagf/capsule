FROM astral/uv:python3.14-trixie-slim

ENV UV_COMPILE_BYTECODE=1

COPY . /app

WORKDIR /app

RUN uv sync --no-dev

EXPOSE 9292

ENTRYPOINT ["uv", "run", "--no-sync", "capsule"]

CMD ["start-server"]
