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
