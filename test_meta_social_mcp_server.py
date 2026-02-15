#!/usr/bin/env python3
"""
Tests for Meta Social MCP Server (Facebook/Instagram)
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent / ".claude" / "skills" / "meta-social-mcp-server" / "scripts"))

from models import (
    ApprovalRequest,
    ApprovalStatus,
    FacebookPage,
    FacebookPost,
    InstagramPost,
    InstagramReel,
    MediaType,
    MetaConfig,
    PostStatus,
)


class TestMetaModels(unittest.TestCase):
    """Test Meta Social data models"""

    def test_media_type_values(self):
        """Test MediaType enum values"""
        self.assertEqual(MediaType.IMAGE.value, "IMAGE")
        self.assertEqual(MediaType.VIDEO.value, "VIDEO")
        self.assertEqual(MediaType.CAROUSEL.value, "CAROUSEL")
        self.assertEqual(MediaType.REEL.value, "REELS")

    def test_post_status_values(self):
        """Test PostStatus enum values"""
        self.assertEqual(PostStatus.DRAFT.value, "draft")
        self.assertEqual(PostStatus.PENDING_APPROVAL.value, "pending_approval")
        self.assertEqual(PostStatus.PUBLISHED.value, "published")

    def test_facebook_page_model(self):
        """Test FacebookPage model"""
        page = FacebookPage(
            id="123456789",
            name="Test Page",
            category="Business",
            followers_count=10000
        )

        self.assertEqual(page.id, "123456789")
        self.assertEqual(page.name, "Test Page")
        self.assertEqual(page.followers_count, 10000)

    def test_facebook_post_to_graph_api_params(self):
        """Test FacebookPost conversion to Graph API params"""
        post = FacebookPost(
            page_id="123456789",
            message="Hello Facebook!",
            link="https://example.com"
        )
        params = post.to_graph_api_params()

        self.assertEqual(params["message"], "Hello Facebook!")
        self.assertEqual(params["link"], "https://example.com")

    def test_facebook_post_scheduled(self):
        """Test scheduled FacebookPost"""
        scheduled_time = datetime(2024, 1, 20, 14, 0, 0)
        post = FacebookPost(
            page_id="123456789",
            message="Scheduled post",
            scheduled_publish_time=scheduled_time
        )
        params = post.to_graph_api_params()

        self.assertIn("scheduled_publish_time", params)
        self.assertEqual(params["published"], False)

    def test_instagram_post_model(self):
        """Test InstagramPost model"""
        post = InstagramPost(
            account_id="17841400000000",
            caption="Hello Instagram! #test",
            media_type=MediaType.IMAGE,
            media_url="https://example.com/image.jpg"
        )

        self.assertEqual(post.account_id, "17841400000000")
        self.assertEqual(post.media_type, MediaType.IMAGE)
        self.assertEqual(post.status, PostStatus.DRAFT)

    def test_instagram_reel_model(self):
        """Test InstagramReel model"""
        reel = InstagramReel(
            account_id="17841400000000",
            video_url="https://example.com/video.mp4",
            caption="Check out this reel!",
            share_to_feed=True
        )

        self.assertEqual(reel.account_id, "17841400000000")
        self.assertTrue(reel.share_to_feed)

    def test_meta_config_defaults(self):
        """Test MetaConfig default values"""
        config = MetaConfig()

        self.assertEqual(config.api_version, "v21.0")
        self.assertEqual(config.timeout_seconds, 30)
        self.assertTrue(config.require_approval_for_posts)
        self.assertTrue(config.require_approval_for_reels)
        self.assertEqual(config.max_text_length, 63206)

    def test_approval_request_to_dict(self):
        """Test ApprovalRequest serialization"""
        request = ApprovalRequest(
            id="meta_approval_123",
            platform="instagram",
            operation="create_post",
            content_type="post",
            data={"caption": "Test"},
            status=ApprovalStatus.PENDING
        )
        result = request.to_dict()

        self.assertEqual(result["id"], "meta_approval_123")
        self.assertEqual(result["platform"], "instagram")
        self.assertEqual(result["status"], "pending")


class TestMetaSocialApprovalWorkflow(unittest.TestCase):
    """Test Meta Social approval workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_meta.db")

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_requires_approval_for_posts(self):
        """Test that posts require approval"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("create_post"))
        self.assertTrue(workflow.requires_approval("schedule_post"))
        self.assertTrue(workflow.requires_approval("facebook_create_post"))
        self.assertTrue(workflow.requires_approval("instagram_create_post"))

    def test_requires_approval_for_reels(self):
        """Test that reels require approval"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("create_reel"))
        self.assertTrue(workflow.requires_approval("instagram_create_reel"))

    def test_create_facebook_approval_request(self):
        """Test creating Facebook approval request"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            platform="facebook",
            operation="create_post",
            content_type="post",
            data={"page_id": "123", "message": "Hello!"}
        )

        self.assertIsNotNone(request.id)
        self.assertTrue(request.id.startswith("meta_approval_"))
        self.assertEqual(request.platform, "facebook")
        self.assertEqual(request.operation, "create_post")

    def test_create_instagram_approval_request(self):
        """Test creating Instagram approval request"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            platform="instagram",
            operation="create_reel",
            content_type="reel",
            data={"account_id": "456", "caption": "New reel!"}
        )

        self.assertEqual(request.platform, "instagram")
        self.assertEqual(request.content_type, "reel")

    def test_get_approval_request(self):
        """Test retrieving approval request"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)
        created = workflow.create_approval_request(
            platform="facebook",
            operation="schedule_post",
            data={"message": "Scheduled"}
        )

        retrieved = workflow.get_request(created.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(created.id, retrieved.id)

    def test_approve_request(self):
        """Test approving a request"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            platform="instagram",
            operation="create_post",
            data={"caption": "Test post"}
        )

        approved = workflow.approve_request(request.id, "social_manager")

        self.assertIsNotNone(approved)
        self.assertEqual(approved.status, ApprovalStatus.APPROVED)
        self.assertEqual(approved.approved_by, "social_manager")

    def test_reject_request(self):
        """Test rejecting a request"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            platform="facebook",
            operation="create_post",
            data={"message": "Bad content"}
        )

        rejected = workflow.reject_request(
            request.id,
            "content_moderator",
            "Content violates guidelines"
        )

        self.assertIsNotNone(rejected)
        self.assertEqual(rejected.status, ApprovalStatus.REJECTED)
        self.assertEqual(rejected.rejection_reason, "Content violates guidelines")

    def test_get_pending_requests_by_platform(self):
        """Test getting pending requests filtered by platform"""
        from approval_workflow import MetaSocialApprovalWorkflow

        workflow = MetaSocialApprovalWorkflow(db_path=self.db_path)

        # Create requests for different platforms
        workflow.create_approval_request(platform="facebook", operation="create_post", data={})
        workflow.create_approval_request(platform="instagram", operation="create_post", data={})
        workflow.create_approval_request(platform="instagram", operation="create_reel", data={})

        # Get Facebook only
        fb_pending = workflow.get_pending_requests(platform="facebook")
        self.assertEqual(len(fb_pending), 1)

        # Get Instagram only
        ig_pending = workflow.get_pending_requests(platform="instagram")
        self.assertEqual(len(ig_pending), 2)

        # Get all
        all_pending = workflow.get_pending_requests()
        self.assertEqual(len(all_pending), 3)


if __name__ == "__main__":
    unittest.main()
