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
