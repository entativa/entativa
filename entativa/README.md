# entativa

> Ex Machina — Private & Confidential
> Video-only client. Rust/Blinc.

## What Entativa is

Video. That's it. No photos, no text posts, no DMs.
The feed is vertical, full-screen, GPU-decoded.
The algorithm is watch-time weighted with a cold-start bias toward new creators.

## gRPC transport

This client uses **raw gRPC** over HTTP/2 via `tonic::Channel`.
Not gRPC-Web — that's for browsers. Native apps get the full protocol:

- Bidirectional streaming (watch events ↔ server)
- Client streaming (batch watch events)
- Server streaming (future: live notification push)
- Lower latency (no base64 framing overhead)

## Auth

Auth is handled entirely by `piercer-auth-ui`.
Entativa never touches tokens directly — it delegates to the shared library.
Login, register, logout sheet, and accounts center are all provided by that lib,
themed with Entativa's palette (`#0A0A0A` + `#FF2D2D`).

## Structure

```
proto/              entativa.proto (copy from piercer-core)
src/
  main.rs           Entry point
  app.rs            Root state — auth init, routing
  config.rs         ENV-based config
  navigation.rs     Route enum
  state.rs          FeedState, upload state
  client.rs         Raw gRPC client (tonic Channel)
  screens/
    feed.rs         Vertical video feed + watch event streaming
    upload.rs       Upload flow — transcode → S3 → finalize
    profile.rs      Profile grid
```

## Quick start

```bash
cp .env.example .env
sudo apt-get install -y protobuf-compiler
cp ../piercer-core/proto/entativa.proto proto/
cargo check
cargo run
```

## IP Notice

Proprietary software — Ex Machina. All rights reserved.
