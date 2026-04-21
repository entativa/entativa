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
