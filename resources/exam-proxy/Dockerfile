FROM rust:alpine AS build

COPY Cargo.toml /src/
COPY Cargo.lock /src/
COPY src/ /src/src

WORKDIR /src
RUN cargo build --release

FROM alpine:latest

RUN apk add --no-cache socat util-linux netcat-openbsd

COPY --from=build /src/target/release/exam-proxy /usr/local/bin
COPY resources/loop.sh /usr/local/bin/connect_to_vulnserv.sh


CMD ["/usr/local/bin/connect_to_vulnserv.sh"]


