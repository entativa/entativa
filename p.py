#!/usr/bin/env python3
"""
scaffold_entativa.py  —  Ex Machina
Scaffolds the Entativa client repository.

Entativa: video-only. No DMs. No photos. Fast.

Usage:
    python3 scaffold_entativa.py [--root ./entativa]
"""

import argparse, textwrap
from pathlib import Path


def w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print(f"  + {path}")


def stub(path: Path, comment: str = "") -> None:
    c = comment or path.stem
    w(path, f"// {c}\n" if path.suffix == ".rs" else f"# {c}\n")


# ─────────────────────────────────────────────────────────────────────────────
# CARGO.TOML
# Raw gRPC via tonic + Channel — NOT gRPC-Web.
# Native Rust apps have full HTTP/2 access. gRPC-Web is for browsers only.
# Bidirectional streaming is available and used (watch events).
# ─────────────────────────────────────────────────────────────────────────────

CARGO_TOML = """\
[package]
name        = "entativa"
version     = "0.1.0"
edition     = "2021"
description = "Entativa — video-only client. Rust/Blinc."

[[bin]]
name = "entativa"
path = "src/main.rs"

[dependencies]
# Async runtime
tokio          = { version = "1",    features = ["full"] }

# Raw gRPC — native client, full HTTP/2, bidirectional streaming available
tonic          = { version = "0.11", features = ["tls", "tls-roots"] }
prost          = { version = "0.12" }

# Shared auth UI (login, register, logout sheet, accounts center)
piercer-auth-ui = { path = "../piercer-auth-ui" }

# Serialisation
serde          = { version = "1",    features = ["derive"] }
serde_json     = { version = "1" }

# Errors / logging
anyhow         = { version = "1" }
thiserror      = { version = "1" }
tracing        = { version = "0.1" }
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# IDs / time
uuid           = { version = "1",    features = ["v4", "serde"] }
chrono         = { version = "0.4",  features = ["serde"] }

# Config
config         = { version = "0.14" }

[build-dependencies]
tonic-build = "0.11"
"""

BUILD_RS = """\
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_client(true)
        .build_server(false)
        .compile(
            &[
                "../piercer-auth-ui/proto/auth.proto",
                "../piercer-auth-ui/proto/shared.proto",
                "proto/entativa.proto",
            ],
            &["../piercer-auth-ui/proto", "proto"],
        )?;
    Ok(())
}
"""

GITIGNORE = """\
/target
Cargo.lock
.env
.env.local
.DS_Store
*.log
"""

ENV_EXAMPLE = """\
# Auth service (raw gRPC, not gRPC-Web)
AUTH_URL=http://localhost:50050

# Entativa service (raw gRPC)
ENTATIVA_URL=http://localhost:50051

RUST_LOG=entativa=debug,tonic=info
"""

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

MAIN_RS = """\
//! Entativa — Ex Machina
//! Video-only client. No DMs. No photos.

mod app;
mod client;
mod config;
mod navigation;
mod screens;
mod state;

pub mod proto {
    pub mod entativa {
        tonic::include_proto!("piercer.entativa");
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let cfg = config::Config::from_env()?;
    let mut app = app::App::init(cfg).await?;

    // TODO: hand off to Blinc runtime
    // blinc::run(app).await
    Ok(())
}
"""

CONFIG_RS = """\
//! Entativa client configuration.

#[derive(Debug, Clone)]
pub struct Config {
    pub auth_url:      String,
    pub entativa_url:  String,
}

impl Config {
    pub fn from_env() -> anyhow::Result<Self> {
        Ok(Self {
            auth_url:     std::env::var("AUTH_URL")
                              .unwrap_or_else(|_| "http://localhost:50050".into()),
            entativa_url: std::env::var("ENTATIVA_URL")
                              .unwrap_or_else(|_| "http://localhost:50051".into()),
        })
    }
}
"""

APP_RS = """\
//! Root app state.
//! Initialises auth, then routes to home feed or auth screens.

use piercer_auth_ui::{AuthUi, AppIdentity, InitResult};
use crate::{
    client::EntativaClient,
    config::Config,
    navigation::Route,
    state::FeedState,
};

pub struct App {
    pub route:   Route,
    pub auth:    AuthUi,
    pub client:  EntativaClient,
    pub feed:    FeedState,
}

impl App {
    pub async fn init(cfg: Config) -> anyhow::Result<Self> {
        let mut auth = AuthUi::new(AppIdentity::Entativa, &cfg.auth_url);
        let client   = EntativaClient::connect(&cfg.entativa_url).await?;
        let feed     = FeedState::default();

        let route = match auth.init().await? {
            InitResult::Authenticated(_) => Route::Feed,
            InitResult::NeedsAuth        => Route::Auth,
        };

        Ok(Self { route, auth, client, feed })
    }

    pub fn navigate(&mut self, route: Route) {
        self.route = route;
    }
}
"""

NAV_RS = """\
//! Client-side navigation.

#[derive(Debug, Clone, PartialEq)]
pub enum Route {
    /// Auth screen — shown when no valid session exists.
    Auth,
    /// Main vertical video feed.
    Feed,
    /// User profile grid.
    Profile { user_id: String },
    /// Video upload flow.
    Upload,
    /// Settings + Accounts Center.
    Settings,
}
"""

STATE_RS = """\
//! Application-level state containers.

use crate::proto::entativa::VideoPayload;

/// Feed state — holds the current video list and cursor for pagination.
#[derive(Debug, Default)]
pub struct FeedState {
    pub videos:      Vec<VideoPayload>,
    pub next_cursor: Option<String>,
    pub loading:     bool,
    pub error:       Option<String>,
}

impl FeedState {
    pub fn set_loading(&mut self, v: bool) { self.loading = v; }

    pub fn append_page(&mut self, videos: Vec<VideoPayload>, next_cursor: String) {
        self.videos.extend(videos);
        self.next_cursor = if next_cursor.is_empty() { None } else { Some(next_cursor) };
        self.loading = false;
    }

    pub fn has_more(&self) -> bool { self.next_cursor.is_some() }
}
"""

CLIENT_RS = """\
//! Entativa gRPC client.
//!
//! Uses raw tonic Channel over HTTP/2 — NOT gRPC-Web.
//! This gives us full bidirectional streaming for watch events.
//!
//! Watch event stream:
//!   Client streams WatchEvent messages as the user watches a video.
//!   Server streams back WatchResponse (recorded: bool).
//!   This is the feed algorithm signal — watch time weighted.

use anyhow::Result;
use tonic::transport::Channel;
use tonic::Request;
use crate::proto::entativa::{
    entativa_service_client::EntativaServiceClient,
    FeedRequest, FeedResponse,
    LikeRequest, LikeResponse,
    CommentRequest, CommentResponse,
    CommentsRequest, CommentsResponse,
    WatchEvent, WatchResponse,
};

pub struct EntativaClient {
    inner: EntativaServiceClient<Channel>,
}

impl EntativaClient {
    /// Connect to the Entativa gRPC service.
    /// Uses raw HTTP/2 — full streaming available.
    pub async fn connect(url: &str) -> Result<Self> {
        let channel = Channel::from_shared(url.to_string())?
            .connect()
            .await?;
        Ok(Self { inner: EntativaServiceClient::new(channel) })
    }

    /// Fetch the next page of the feed for a user.
    pub async fn get_feed(
        &mut self,
        user_id: &str,
        cursor:  Option<&str>,
        limit:   i32,
    ) -> Result<FeedResponse> {
        let res = self.inner.get_feed(FeedRequest {
            user_id: user_id.into(),
            cursor:  cursor.unwrap_or("").into(),
            limit,
        }).await?.into_inner();
        Ok(res)
    }

    /// Like or unlike a video.
    pub async fn like_video(&mut self, user_id: &str, video_id: &str) -> Result<LikeResponse> {
        Ok(self.inner.like_video(LikeRequest {
            user_id:  user_id.into(),
            video_id: video_id.into(),
        }).await?.into_inner())
    }

    /// Post a comment on a video.
    pub async fn post_comment(
        &mut self,
        video_id:  &str,
        author_id: &str,
        text:      &str,
    ) -> Result<CommentResponse> {
        Ok(self.inner.post_comment(CommentRequest {
            video_id:  video_id.into(),
            author_id: author_id.into(),
            text:      text.into(),
        }).await?.into_inner())
    }

    /// Bidirectional streaming watch event recorder.
    ///
    /// The caller provides a stream of WatchEvent messages
    /// (sent as the user watches — position, duration, completion).
    /// The server streams back WatchResponse for each event recorded.
    ///
    /// This is the primary feed algorithm signal.
    /// Keep this stream open for the duration of a watch session.
    pub async fn stream_watch_events(
        &mut self,
        events: impl futures::Stream<Item = WatchEvent> + Send + 'static,
    ) -> Result<tonic::Streaming<WatchResponse>> {
        let res = self.inner.record_watch(Request::new(events)).await?;
        Ok(res.into_inner())
    }
}
"""

FEED_SCREEN_RS = """\
//! Feed screen — vertical video feed.
//!
//! Layout (Blinc tree):
//!   VerticalPager (snap per item, preloads ±1 item)
//!     └── VideoCard (per video)
//!           ├── VideoPlayer (GPU decoded, H.265)
//!           ├── RightActions (overlay)
//!           │     ├── LikeButton  (heart, like_count)
//!           │     ├── CommentButton (bubble, reply_count)
//!           │     └── ShareButton
//!           └── BottomInfo (overlay)
//!                 ├── @handle (author)
//!                 └── Caption (truncated, expand on tap)
//!
//! Performance contract:
//!   First frame rendered within 300ms of app open on mid-range Android.
//!   Next video preloaded while current is playing.
//!   Watch event stream kept open for duration of session.

use crate::{
    client::EntativaClient,
    proto::entativa::{VideoPayload, WatchEvent},
    state::FeedState,
};

pub struct FeedScreen;

impl FeedScreen {
    /// Called when feed becomes visible.
    /// Fetches initial page and opens the watch event stream.
    pub async fn on_enter(
        client:  &mut EntativaClient,
        state:   &mut FeedState,
        user_id: &str,
    ) -> anyhow::Result<()> {
        state.set_loading(true);
        let page = client.get_feed(user_id, None, 10).await?;
        state.append_page(page.videos, page.next_cursor);
        // TODO: open bidirectional watch event stream
        // let event_tx = open_watch_stream(client).await?;
        Ok(())
    }

    /// Called when the user scrolls to the last video — fetch next page.
    pub async fn load_more(
        client:  &mut EntativaClient,
        state:   &mut FeedState,
        user_id: &str,
    ) -> anyhow::Result<()> {
        if state.loading || !state.has_more() { return Ok(()); }
        state.set_loading(true);
        let cursor = state.next_cursor.as_deref();
        let page   = client.get_feed(user_id, cursor, 10).await?;
        state.append_page(page.videos, page.next_cursor);
        Ok(())
    }

    /// Emit a watch event for the current video.
    /// Called periodically while a video is playing.
    pub fn make_watch_event(
        user_id:  &str,
        video_id: &str,
        watch_ms: i32,
        completed: bool,
    ) -> WatchEvent {
        WatchEvent {
            user_id:   user_id.into(),
            video_id:  video_id.into(),
            watch_ms,
            completed,
        }
    }
}
"""

UPLOAD_SCREEN_RS = """\
//! Upload screen — video upload flow.
//!
//! Flow:
//!   1. User picks video from device gallery or camera
//!   2. Client-side transcode to H.265/HEVC (GPU via Blinc render pipeline)
//!   3. InitUpload RPC → get presigned S3 URL
//!   4. Upload directly to S3 (chunked, resumable)
//!   5. FinalizeUpload RPC → server processes, generates thumbnail, queues transcode fallback
//!   6. Navigate back to feed
//!
//! The transcode happens on-device before upload.
//! This keeps upload sizes small and ensures consistent codec across all videos.

use crate::client::EntativaClient;

pub struct UploadScreenState {
    pub video_path:    Option<std::path::PathBuf>,
    pub caption:       String,
    pub tags:          Vec<String>,
    pub progress:      f32,   // 0.0–1.0
    pub stage:         UploadStage,
    pub error:         Option<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum UploadStage {
    Idle,
    Transcoding,
    Uploading,
    Finalizing,
    Done,
}

impl Default for UploadScreenState {
    fn default() -> Self {
        Self {
            video_path: None,
            caption:    String::new(),
            tags:       Vec::new(),
            progress:   0.0,
            stage:      UploadStage::Idle,
            error:      None,
        }
    }
}

impl UploadScreenState {
    pub fn can_upload(&self) -> bool {
        self.video_path.is_some() && self.stage == UploadStage::Idle
    }

    pub async fn start_upload(
        &mut self,
        _client:  &mut EntativaClient,
        _user_id: &str,
    ) -> anyhow::Result<()> {
        // TODO:
        // 1. self.stage = UploadStage::Transcoding
        //    transcode_to_h265(&self.video_path.unwrap())
        // 2. self.stage = UploadStage::Uploading
        //    client.init_upload(...) → presigned_url
        //    upload_to_s3(presigned_url, transcoded_file, |progress| self.progress = progress)
        // 3. self.stage = UploadStage::Finalizing
        //    client.finalize_upload(upload_id, caption, tags)
        // 4. self.stage = UploadStage::Done
        Ok(())
    }
}
"""

PROFILE_SCREEN_RS = """\
//! Profile screen — user's video grid + stats.
//!
//! Layout:
//!   Screen
//!     ├── ProfileHeader
//!     │     ├── Avatar (circular, 72px)
//!     │     ├── @handle + display_name
//!     │     ├── StatsRow (videos | followers | following)
//!     │     └── FollowButton (if viewing another user)
//!     └── VideoGrid (3-column, square thumbnails, tap → open video)

// TODO: implement profile screen state and data fetching
"""

README = """\
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
"""


def scaffold(root: Path) -> None:
    print(f"\n⚡ Scaffolding Entativa → {root}\n")

    w(root / "Cargo.toml",   CARGO_TOML)
    w(root / "build.rs",     BUILD_RS)
    w(root / ".gitignore",   GITIGNORE)
    w(root / ".env.example", ENV_EXAMPLE)
    w(root / "README.md",    README)

    stub(root / "proto" / "entativa.proto",
         "Copy from piercer-core/proto/entativa.proto")

    w(root / "src" / "main.rs",       MAIN_RS)
    w(root / "src" / "config.rs",     CONFIG_RS)
    w(root / "src" / "app.rs",        APP_RS)
    w(root / "src" / "navigation.rs", NAV_RS)
    w(root / "src" / "state.rs",      STATE_RS)
    w(root / "src" / "client.rs",     CLIENT_RS)

    w(root / "src" / "screens" / "mod.rs",
      "pub mod feed;\npub mod upload;\npub mod profile;\n")
    w(root / "src" / "screens" / "feed.rs",    FEED_SCREEN_RS)
    w(root / "src" / "screens" / "upload.rs",  UPLOAD_SCREEN_RS)
    w(root / "src" / "screens" / "profile.rs", PROFILE_SCREEN_RS)

    stub(root / "tests" / "feed_tests.rs",   "Feed pagination + watch event tests")
    stub(root / "tests" / "upload_tests.rs", "Upload flow tests")

    print(f"\n── Done. {root}\n")
    print("  cp ../piercer-core/proto/entativa.proto proto/")
    print("  cargo check\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="./entativa")
    args = parser.parse_args()
    scaffold(Path(args.root).resolve())


if __name__ == "__main__":
    main()
