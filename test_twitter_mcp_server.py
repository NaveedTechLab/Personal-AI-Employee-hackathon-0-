#!/usr/bin/env python3
"""
Tests for Twitter (X) MCP Server
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent / ".claude" / "skills" / "twitter-mcp-server" / "scripts"))

from models import (
    ApprovalRequest,
    ApprovalStatus,
    MediaType,
    MediaUpload,
    RateLimitInfo,
    Tweet,
    TweetThread,
    TweetType,
    TwitterConfig,
)


class TestTwitterModels(unittest.TestCase):
    """Test Twitter data models"""

    def test_media_type_values(self):
        """Test MediaType enum values"""
        self.assertEqual(MediaType.IMAGE.value, "image")
        self.assertEqual(MediaType.VIDEO.value, "video")
        self.assertEqual(MediaType.GIF.value, "animated_gif")

    def test_tweet_type_values(self):
        """Test TweetType enum values"""
        self.assertEqual(TweetType.TWEET.value, "tweet")
        self.assertEqual(TweetType.REPLY.value, "reply")
        self.assertEqual(TweetType.THREAD.value, "thread")

    def test_tweet_text_validation(self):
        """Test Tweet text length validation"""
        # Valid tweet
        tweet = Tweet(text="Hello Twitter!")
        self.assertEqual(tweet.text, "Hello Twitter!")

        # Test max length (280)
        long_text = "x" * 280
        tweet = Tweet(text=long_text)
        self.assertEqual(len(tweet.text), 280)

        # Too long should raise error
        with self.assertRaises(ValueError):
            Tweet(text="x" * 281)

    def test_tweet_to_api_payload_simple(self):
        """Test simple Tweet API payload"""
        tweet = Tweet(text="Hello World!")
        payload = tweet.to_api_payload()

        self.assertEqual(payload["text"], "Hello World!")
        self.assertNotIn("reply", payload)
        self.assertNotIn("media", payload)

    def test_tweet_to_api_payload_with_reply(self):
        """Test Tweet API payload with reply"""
        tweet = Tweet(
            text="This is a reply",
            reply_to_tweet_id="1234567890"
        )
        payload = tweet.to_api_payload()

        self.assertIn("reply", payload)
        self.assertEqual(payload["reply"]["in_reply_to_tweet_id"], "1234567890")

    def test_tweet_to_api_payload_with_media(self):
        """Test Tweet API payload with media"""
        tweet = Tweet(
            text="Check this out!",
            media_ids=["111111", "222222"]
        )
        payload = tweet.to_api_payload()

        self.assertIn("media", payload)
        self.assertEqual(payload["media"]["media_ids"], ["111111", "222222"])

    def test_tweet_thread_validation(self):
        """Test TweetThread validation"""
        # Valid thread
        thread = TweetThread(tweets=[
            Tweet(text="First tweet"),
            Tweet(text="Second tweet")
        ])
        self.assertEqual(len(thread.tweets), 2)

        # Too short
        with self.assertRaises(ValueError):
            TweetThread(tweets=[Tweet(text="Only one")])

    def test_media_upload_model(self):
        """Test MediaUpload model"""
        upload = MediaUpload(
            media_id="1234567890",
            media_type=MediaType.IMAGE,
            url="https://example.com/image.jpg",
            alt_text="A test image"
        )

        self.assertEqual(upload.media_id, "1234567890")
        self.assertEqual(upload.media_type, MediaType.IMAGE)
        self.assertEqual(upload.alt_text, "A test image")

    def test_rate_limit_info(self):
        """Test RateLimitInfo model"""
        reset_time = datetime.now() + timedelta(minutes=10)
        info = RateLimitInfo(
            endpoint="tweets/create",
            limit=200,
            remaining=150,
            reset_at=reset_time,
            used=50
        )

        self.assertEqual(info.limit, 200)
        self.assertEqual(info.remaining, 150)
        self.assertEqual(info.percentage_used, 25.0)
        self.assertGreater(info.seconds_until_reset, 0)

    def test_twitter_config_defaults(self):
        """Test TwitterConfig default values"""
        config = TwitterConfig()

        self.assertEqual(config.api_version, "2")
        self.assertEqual(config.timeout_seconds, 30)
        self.assertTrue(config.require_approval_for_tweets)
        self.assertTrue(config.require_approval_for_threads)
        self.assertEqual(config.warn_at_percentage, 80)
        self.assertEqual(config.block_at_percentage, 95)

    def test_approval_request_to_dict(self):
        """Test ApprovalRequest serialization"""
        request = ApprovalRequest(
            id="twitter_approval_123",
            operation="create_tweet",
            tweet_type=TweetType.TWEET,
            data={"text": "Hello!"},
            character_count=6,
            status=ApprovalStatus.PENDING
        )
        result = request.to_dict()

        self.assertEqual(result["id"], "twitter_approval_123")
        self.assertEqual(result["operation"], "create_tweet")
        self.assertEqual(result["character_count"], 6)
        self.assertEqual(result["status"], "pending")


class TestRateLimiter(unittest.TestCase):
    """Test Twitter rate limiter"""

    def test_rate_limit_check_allowed(self):
        """Test rate limit check when allowed"""
        from rate_limiter import RateLimiter

        limiter = RateLimiter()
        allowed, reason = limiter.check_rate_limit("tweets/create")

        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_rate_limit_tracking(self):
        """Test rate limit tracking"""
        from rate_limiter import RateLimiter

        limiter = RateLimiter()

        # Record some requests
        for _ in range(10):
            limiter.record_request("tweets/create")

        info = limiter.get_rate_limit_info("tweets/create")
        self.assertEqual(info["used"], 10)

    def test_rate_limit_update_from_headers(self):
        """Test updating rate limits from headers"""
        from rate_limiter import RateLimiter

        limiter = RateLimiter()
        headers = {
            "x-rate-limit-limit": "200",
            "x-rate-limit-remaining": "150",
            "x-rate-limit-reset": str(int((datetime.now() + timedelta(minutes=10)).timestamp()))
        }

        limiter.update_from_headers("tweets/create", headers)
        info = limiter.get_rate_limit_info("tweets/create")

        self.assertEqual(info["limit"], 200)
        self.assertEqual(info["remaining"], 150)

    def test_rate_limit_reset(self):
        """Test resetting rate limits"""
        from rate_limiter import RateLimiter

        limiter = RateLimiter()

        # Record requests
        for _ in range(5):
            limiter.record_request("tweets/create")

        # Reset
        limiter.reset_endpoint("tweets/create")
        info = limiter.get_rate_limit_info("tweets/create")

        self.assertEqual(info["used"], 0)


class TestTwitterApprovalWorkflow(unittest.TestCase):
    """Test Twitter approval workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_twitter.db")

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_requires_approval_for_tweets(self):
        """Test that tweets require approval"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("create_tweet"))

    def test_requires_approval_for_threads(self):
        """Test that threads require approval"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("create_thread"))

    def test_requires_approval_for_delete(self):
        """Test that delete requires approval"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("delete_tweet"))

    def test_create_tweet_approval_request(self):
        """Test creating tweet approval request"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="create_tweet",
            tweet_type=TweetType.TWEET,
            data={"text": "Hello Twitter!"},
            character_count=15
        )

        self.assertIsNotNone(request.id)
        self.assertTrue(request.id.startswith("twitter_approval_"))
        self.assertEqual(request.operation, "create_tweet")
        self.assertEqual(request.character_count, 15)

    def test_create_thread_approval_request(self):
        """Test creating thread approval request"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="create_thread",
            tweet_type=TweetType.THREAD,
            data={"tweets": [{"text": "1/2 First"}, {"text": "2/2 Second"}]},
            character_count=25
        )

        self.assertEqual(request.tweet_type, TweetType.THREAD)

    def test_approve_request(self):
        """Test approving a request"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="create_tweet",
            data={"text": "Test tweet"}
        )

        approved = workflow.approve_request(request.id, "social_admin")

        self.assertIsNotNone(approved)
        self.assertEqual(approved.status, ApprovalStatus.APPROVED)
        self.assertEqual(approved.approved_by, "social_admin")

    def test_reject_request(self):
        """Test rejecting a request"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="create_tweet",
            data={"text": "Bad content"}
        )

        rejected = workflow.reject_request(
            request.id,
            "moderator",
            "Content policy violation"
        )

        self.assertIsNotNone(rejected)
        self.assertEqual(rejected.status, ApprovalStatus.REJECTED)
        self.assertEqual(rejected.rejection_reason, "Content policy violation")

    def test_get_pending_requests(self):
        """Test getting pending requests"""
        from approval_workflow import TwitterApprovalWorkflow

        workflow = TwitterApprovalWorkflow(db_path=self.db_path)

        # Create multiple requests
        workflow.create_approval_request(operation="create_tweet", data={"text": "Tweet 1"})
        workflow.create_approval_request(operation="create_tweet", data={"text": "Tweet 2"})
        req3 = workflow.create_approval_request(operation="create_thread", data={})

        # Approve one
        workflow.approve_request(req3.id, "admin")

        pending = workflow.get_pending_requests()
        self.assertEqual(len(pending), 2)


if __name__ == "__main__":
    unittest.main()
