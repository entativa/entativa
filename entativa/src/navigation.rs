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
