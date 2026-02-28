#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成工具
支持文本生成视频、图片生成视频等功能
"""

import logging
import os
from typing import Optional
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk.video import (
    VideoGenerationClient,
    TextContent,
    ImageURLContent,
    ImageURL
)
from coze_coding_dev_sdk import APIError

logger = logging.getLogger(__name__)


@tool
def generate_video_from_text(
    prompt: str,
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    watermark: bool = False,
    generate_audio: bool = True,
    runtime: ToolRuntime = None
) -> str:
    """
    根据文本描述生成视频

    Args:
        prompt: 视频的文本描述（中文或英文）
        resolution: 视频分辨率，可选 "480p", "720p", "1080p"，默认 "720p"
        ratio: 视频比例，可选 "16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"，默认 "16:9"
        duration: 视频时长（秒），4-12秒，默认 5秒
        watermark: 是否添加水印，默认 False
        generate_audio: 是否生成音频，默认 True

    Returns:
        生成的视频 URL 和相关信息
    """
    ctx = runtime.context if runtime else new_context(method="video.generate_text")

    try:
        client = VideoGenerationClient(ctx=ctx)

        logger.info(f"开始生成视频: {prompt}")

        video_url, response, _ = client.video_generation(
            content_items=[TextContent(text=prompt)],
            model="doubao-seedance-1-5-pro-251215",
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            watermark=watermark,
            generate_audio=generate_audio,
            max_wait_time=600
        )

        if video_url:
            result = f"✅ 视频生成成功！\n"
            result += f"📹 视频URL: {video_url}\n"
            result += f"📝 描述: {prompt}\n"
            result += f"🎨 分辨率: {resolution}\n"
            result += f"📏 比例: {ratio}\n"
            result += f"⏱️ 时长: {duration}秒\n"
            if response.get('usage'):
                result += f"💰 使用Token: {response['usage'].get('total_tokens', 0)}\n"

            logger.info(f"视频生成成功: {video_url}")
            return result
        else:
            error_msg = f"❌ 视频生成失败\n"
            error_msg += f"任务状态: {response.get('status', 'unknown')}\n"
            error_msg += f"请检查描述是否合适，或稍后重试"

            logger.error(f"视频生成失败: {response}")
            return error_msg

    except APIError as e:
        error_msg = f"❌ API 错误: {str(e)}\n"
        error_msg += f"可能原因: API 配置错误或权限不足"

        logger.error(f"视频生成 API 错误: {str(e)}")
        return error_msg
    except Exception as e:
        error_msg = f"❌ 视频生成异常: {str(e)}"

        logger.error(f"视频生成异常: {str(e)}", exc_info=True)
        return error_msg


@tool
def generate_video_from_image(
    image_url: str,
    prompt: Optional[str] = None,
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    watermark: bool = False,
    runtime: ToolRuntime = None
) -> str:
    """
    根据图片生成视频（首帧动画）

    Args:
        image_url: 首帧图片的 URL
        prompt: 可选的文本描述，用于指导动画效果
        resolution: 视频分辨率，可选 "480p", "720p", "1080p"，默认 "720p"
        ratio: 视频比例，可选 "16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"，默认 "16:9"
        duration: 视频时长（秒），4-12秒，默认 5秒
        watermark: 是否添加水印，默认 False

    Returns:
        生成的视频 URL 和相关信息
    """
    ctx = runtime.context if runtime else new_context(method="video.generate_image")

    try:
        client = VideoGenerationClient(ctx=ctx)

        logger.info(f"开始从图片生成视频: {image_url}")

        content_items = [
            ImageURLContent(
                image_url=ImageURL(url=image_url),
                role="first_frame"
            )
        ]

        if prompt:
            content_items.insert(0, TextContent(text=prompt))

        video_url, response, _ = client.video_generation(
            content_items=content_items,
            model="doubao-seedance-1-5-pro-251215",
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            watermark=watermark,
            max_wait_time=600
        )

        if video_url:
            result = f"✅ 视频生成成功！\n"
            result += f"📹 视频URL: {video_url}\n"
            result += f"🖼️ 源图片: {image_url}\n"
            if prompt:
                result += f"📝 描述: {prompt}\n"
            result += f"🎨 分辨率: {resolution}\n"
            result += f"📏 比例: {ratio}\n"
            result += f"⏱️ 时长: {duration}秒\n"

            logger.info(f"视频生成成功: {video_url}")
            return result
        else:
            error_msg = f"❌ 视频生成失败\n"
            error_msg += f"任务状态: {response.get('status', 'unknown')}\n"
            error_msg += f"请检查图片 URL 是否有效"

            logger.error(f"视频生成失败: {response}")
            return error_msg

    except APIError as e:
        error_msg = f"❌ API 错误: {str(e)}\n"
        error_msg += f"可能原因: API 配置错误或权限不足"

        logger.error(f"视频生成 API 错误: {str(e)}")
        return error_msg
    except Exception as e:
        error_msg = f"❌ 视频生成异常: {str(e)}"

        logger.error(f"视频生成异常: {str(e)}", exc_info=True)
        return error_msg


@tool
def generate_video_between_images(
    first_image_url: str,
    last_image_url: str,
    prompt: Optional[str] = None,
    resolution: str = "720p",
    ratio: str = "16:9",
    duration: int = 5,
    watermark: bool = False,
    runtime: ToolRuntime = None
) -> str:
    """
    根据首尾帧图片生成视频（平滑过渡）

    Args:
        first_image_url: 首帧图片的 URL
        last_image_url: 尾帧图片的 URL
        prompt: 可选的文本描述，用于指导过渡效果
        resolution: 视频分辨率，可选 "480p", "720p", "1080p"，默认 "720p"
        ratio: 视频比例，可选 "16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"，默认 "16:9"
        duration: 视频时长（秒），4-12秒，默认 5秒
        watermark: 是否添加水印，默认 False

    Returns:
        生成的视频 URL 和相关信息
    """
    ctx = runtime.context if runtime else new_context(method="video.generate_between")

    try:
        client = VideoGenerationClient(ctx=ctx)

        logger.info(f"开始从首尾帧生成视频")

        content_items = [
            TextContent(text=prompt or "Smooth transition between frames"),
            ImageURLContent(
                image_url=ImageURL(url=first_image_url),
                role="first_frame"
            ),
            ImageURLContent(
                image_url=ImageURL(url=last_image_url),
                role="last_frame"
            )
        ]

        video_url, response, _ = client.video_generation(
            content_items=content_items,
            model="doubao-seedance-1-5-pro-251215",
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            watermark=watermark,
            max_wait_time=600
        )

        if video_url:
            result = f"✅ 视频生成成功！\n"
            result += f"📹 视频URL: {video_url}\n"
            result += f"🖼️ 首帧: {first_image_url}\n"
            result += f"🖼️ 尾帧: {last_image_url}\n"
            if prompt:
                result += f"📝 描述: {prompt}\n"
            result += f"🎨 分辨率: {resolution}\n"
            result += f"📏 比例: {ratio}\n"
            result += f"⏱️ 时长: {duration}秒\n"

            logger.info(f"视频生成成功: {video_url}")
            return result
        else:
            error_msg = f"❌ 视频生成失败\n"
            error_msg += f"任务状态: {response.get('status', 'unknown')}\n"
            error_msg += f"请检查图片 URL 是否有效"

            logger.error(f"视频生成失败: {response}")
            return error_msg

    except APIError as e:
        error_msg = f"❌ API 错误: {str(e)}\n"
        error_msg += f"可能原因: API 配置错误或权限不足"

        logger.error(f"视频生成 API 错误: {str(e)}")
        return error_msg
    except Exception as e:
        error_msg = f"❌ 视频生成异常: {str(e)}"

        logger.error(f"视频生成异常: {str(e)}", exc_info=True)
        return error_msg


# 导出工具
__all__ = [
    "generate_video_from_text",
    "generate_video_from_image",
    "generate_video_between_images"
]
