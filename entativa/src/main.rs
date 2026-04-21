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
