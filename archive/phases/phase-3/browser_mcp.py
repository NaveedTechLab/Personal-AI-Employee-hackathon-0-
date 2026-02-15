"""
Browser MCP Server for Phase 3 - Autonomous Employee (Gold Tier)
Handles browser-based actions like navigating websites, filling forms, and scraping data.
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from fastmcp import FastMCP, Tool
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright
import tempfile
import os


class NavigateRequest(BaseModel):
    """Request model for navigating to a URL."""
    url: str = Field(..., description="URL to navigate to")
    wait_for_load: bool = Field(True, description="Whether to wait for page load")


class FillFormRequest(BaseModel):
    """Request model for filling a form."""
    url: str = Field(..., description="URL of the page containing the form")
    form_data: Dict[str, str] = Field(..., description="Dictionary of field names to values")
    submit_button_selector: Optional[str] = Field(None, description="Selector for submit button")


class ScrapeDataRequest(BaseModel):
    """Request model for scraping data from a page."""
    url: str = Field(..., description="URL to scrape data from")
    selectors: Dict[str, str] = Field(..., description="Dictionary of data names to CSS selectors")


class ScreenshotRequest(BaseModel):
    """Request model for taking a screenshot."""
    url: str = Field(..., description="URL to take screenshot of")
    element_selector: Optional[str] = Field(None, description="Specific element to screenshot")
    full_page: bool = Field(False, description="Whether to take full page screenshot")


class BrowserMCP:
    """
    MCP Server for handling browser-based actions like navigating websites,
    filling forms, and scraping data.
    """

    def __init__(self):
        """Initialize the Browser MCP server."""
        self.mcp = FastMCP(
            name="browser-mcp",
            description="Handles browser-based actions like navigating websites, filling forms, and scraping data"
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Register tools
        self._register_tools()

        # Track active browsers to prevent resource leaks
        self.active_browsers = {}

    def _register_tools(self):
        """Register tools for the browser MCP server."""
        self.mcp.tool(
            name="navigate_to_url",
            description="Navigate to a specific URL",
            input_model=NavigateRequest
        )(self.navigate_to_url)

        self.mcp.tool(
            name="fill_form",
            description="Fill out a form on a webpage",
            input_model=FillFormRequest
        )(self.fill_form)

        self.mcp.tool(
            name="scrape_data",
            description="Scrape data from a webpage using CSS selectors",
            input_model=ScrapeDataRequest
        )(self.scrape_data)

        self.mcp.tool(
            name="take_screenshot",
            description="Take a screenshot of a webpage or specific element",
            input_model=ScreenshotRequest
        )(self.take_screenshot)

    async def navigate_to_url(self, request: NavigateRequest) -> Dict[str, Any]:
        """
        Navigate to a specific URL.

        Args:
            request: Request containing the URL to navigate to

        Returns:
            Dictionary with navigation results
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="browser.navigation",
                target=request.url,
                approval_status="pending",
                result="in_progress",
                context_correlation=f"nav_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "url": request.url,
                    "wait_for_load": request.wait_for_load
                }
            )

            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "browser.navigation",
                request.url
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="browser.navigation",
                    target=request.url,
                    approval_status="rejected",
                    result="blocked_by_safety",
                    context_correlation=log_id,
                    additional_metadata={
                        "reason": "safety_boundary_violation",
                        "compliance": compliance
                    }
                )
                return {
                    "success": False,
                    "error": "Navigation blocked by safety boundaries",
                    "log_id": log_id
                }

            # In a real implementation, we would use Playwright to navigate
            # For this example, we'll simulate the navigation
            self.logger.info(f"Simulating navigation to: {request.url}")

            # Simulate navigation
            await asyncio.sleep(0.5)  # Simulate page load time

            # Log successful completion
            log_mcp_action(
                action_type="browser.navigation",
                target=request.url,
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "url": request.url,
                    "status_code": 200
                }
            )

            return {
                "success": True,
                "url": request.url,
                "status": "navigated",
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error navigating to URL {request.url}: {str(e)}")

            log_mcp_action(
                action_type="browser.navigation",
                target=request.url,
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"nav_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "url": request.url
                }
            )

            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }

    async def fill_form(self, request: FillFormRequest) -> Dict[str, Any]:
        """
        Fill out a form on a webpage.

        Args:
            request: Request containing form data and URL

        Returns:
            Dictionary with form filling results
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="browser.form_fill",
                target=request.url,
                approval_status="pending",
                result="in_progress",
                context_correlation=f"form_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "url": request.url,
                    "form_fields": list(request.form_data.keys()),
                    "submit_button": request.submit_button_selector
                }
            )

            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "browser.form_fill",
                request.url
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="browser.form_fill",
                    target=request.url,
                    approval_status="rejected",
                    result="blocked_by_safety",
                    context_correlation=log_id,
                    additional_metadata={
                        "reason": "safety_boundary_violation",
                        "compliance": compliance
                    }
                )
                return {
                    "success": False,
                    "error": "Form filling blocked by safety boundaries",
                    "log_id": log_id
                }

            # Check if approval is required for this type of action
            requires_approval = safety_enforcer.check_action_allowed(
                safety_enforcer._get_boundary_for_action("browser.form_fill"),
                {"action": "fill_form", "url": request.url, "fields": list(request.form_data.keys())}
            ).allowed == False

            if requires_approval:
                # Request human approval before filling form
                approval_result = safety_enforcer.request_human_approval(
                    safety_enforcer._get_boundary_for_action("browser.form_fill"),
                    {"action": "fill_form", "url": request.url, "fields": list(request.form_data.keys())}
                )

                if not approval_result:
                    log_mcp_action(
                        action_type="browser.form_fill",
                        target=request.url,
                        approval_status="pending_approval",
                        result="waiting_for_approval",
                        context_correlation=log_id,
                        additional_metadata={
                            "approval_required": True,
                            "url": request.url
                        }
                    )
                    return {
                        "success": False,
                        "error": "Form filling requires human approval",
                        "log_id": log_id,
                        "requires_approval": True
                    }

            # In a real implementation, we would use Playwright to fill the form
            # For this example, we'll simulate the form filling
            self.logger.info(f"Simulating form filling at: {request.url}")
            self.logger.info(f"Form data: {request.form_data}")

            # Simulate form filling
            await asyncio.sleep(0.3)  # Simulate interaction time

            # Log successful completion
            log_mcp_action(
                action_type="browser.form_fill",
                target=request.url,
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "url": request.url,
                    "filled_fields": list(request.form_data.keys()),
                    "submitted": bool(request.submit_button_selector)
                }
            )

            return {
                "success": True,
                "url": request.url,
                "filled_fields": list(request.form_data.keys()),
                "submitted": bool(request.submit_button_selector),
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error filling form at {request.url}: {str(e)}")

            log_mcp_action(
                action_type="browser.form_fill",
                target=request.url,
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"form_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "url": request.url
                }
            )

            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }

    async def scrape_data(self, request: ScrapeDataRequest) -> Dict[str, Any]:
        """
        Scrape data from a webpage using CSS selectors.

        Args:
            request: Request containing URL and selectors

        Returns:
            Dictionary with scraped data
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="browser.scraping",
                target=request.url,
                approval_status="read_only",
                result="success",
                context_correlation=f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "url": request.url,
                    "selectors_used": list(request.selectors.keys())
                }
            )

            # Since this is a read-only operation, no approval needed
            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "browser.scraping",
                request.url
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="browser.scraping",
                    target=request.url,
                    approval_status="rejected",
                    result="blocked_by_safety",
                    context_correlation=log_id,
                    additional_metadata={
                        "reason": "safety_boundary_violation",
                        "compliance": compliance
                    }
                )
                return {
                    "success": False,
                    "error": "Data scraping blocked by safety boundaries",
                    "log_id": log_id
                }

            # In a real implementation, we would use Playwright to scrape data
            # For this example, we'll return simulated data based on selectors
            scraped_data = {}
            for data_name, selector in request.selectors.items():
                # Simulate scraping data based on selector
                if "price" in data_name.lower() or "cost" in data_name.lower():
                    scraped_data[data_name] = "$99.99"
                elif "title" in data_name.lower() or "name" in data_name.lower():
                    scraped_data[data_name] = "Sample Product Title"
                elif "description" in data_name.lower():
                    scraped_data[data_name] = "This is a sample product description."
                else:
                    scraped_data[data_name] = f"Sample value for {selector}"

            return {
                "success": True,
                "url": request.url,
                "scraped_data": scraped_data,
                "selectors_used": list(request.selectors.keys()),
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error scraping data from {request.url}: {str(e)}")

            log_mcp_action(
                action_type="browser.scraping",
                target=request.url,
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "url": request.url
                }
            )

            return {
                "success": False,
                "error": str(e),
                "scraped_data": {},
                "log_id": None
            }

    async def take_screenshot(self, request: ScreenshotRequest) -> Dict[str, Any]:
        """
        Take a screenshot of a webpage or specific element.

        Args:
            request: Request containing URL and screenshot parameters

        Returns:
            Dictionary with screenshot result
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="browser.screenshot",
                target=request.url,
                approval_status="read_only",
                result="success",
                context_correlation=f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "url": request.url,
                    "element_selector": request.element_selector,
                    "full_page": request.full_page
                }
            )

            # Since this is a read-only operation, no approval needed
            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "browser.screenshot",
                request.url
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="browser.screenshot",
                    target=request.url,
                    approval_status="rejected",
                    result="blocked_by_safety",
                    context_correlation=log_id,
                    additional_metadata={
                        "reason": "safety_boundary_violation",
                        "compliance": compliance
                    }
                )
                return {
                    "success": False,
                    "error": "Screenshot blocked by safety boundaries",
                    "log_id": log_id
                }

            # Create a temporary file for the screenshot
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                screenshot_path = tmp_file.name

            # In a real implementation, we would use Playwright to take the screenshot
            # For this example, we'll simulate creating a dummy screenshot file
            with open(screenshot_path, 'wb') as f:
                # Write a dummy PNG file header (not a real image, just for simulation)
                f.write(b'\x89PNG\r\n\x1a\n')  # PNG header
                f.write(b'Dummy screenshot content for ')  # Dummy content
                f.write(request.url.encode('utf-8'))

            return {
                "success": True,
                "url": request.url,
                "screenshot_path": screenshot_path,
                "element_selector": request.element_selector,
                "full_page": request.full_page,
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error taking screenshot of {request.url}: {str(e)}")

            log_mcp_action(
                action_type="browser.screenshot",
                target=request.url,
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "url": request.url
                }
            )

            return {
                "success": False,
                "error": str(e),
                "screenshot_path": None,
                "log_id": None
            }

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the browser MCP server.

        Returns:
            Dictionary with server information
        """
        return {
            "name": "Browser MCP Server",
            "version": "1.0.0",
            "description": "Handles browser-based actions like navigating websites, filling forms, and scraping data",
            "responsibility": "Browser automation only",
            "available_tools": [
                "navigate_to_url",
                "fill_form",
                "scrape_data",
                "take_screenshot"
            ],
            "status": "running",
            "started_at": datetime.now().isoformat()
        }

    async def run(self, port: int = 8001):
        """
        Run the Browser MCP server.

        Args:
            port: Port to run the server on
        """
        self.logger.info(f"Starting Browser MCP Server on port {port}")
        await self.mcp.run(port=port)


def get_browser_mcp_instance() -> BrowserMCP:
    """
    Factory function to get a BrowserMCP instance.

    Returns:
        BrowserMCP instance
    """
    return BrowserMCP()


if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="Browser MCP Server")
    parser.add_argument("--port", type=int, default=8001, help="Port to run the server on")
    args = parser.parse_args()

    async def main():
        browser_mcp = get_browser_mcp_instance()

        print("Browser MCP Server Info:")
        info = browser_mcp.get_server_info()
        for key, value in info.items():
            print(f"  {key}: {value}")

        print(f"\nStarting server on port {args.port}...")
        await browser_mcp.run(port=args.port)

    # Run the server
    asyncio.run(main())