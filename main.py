import os
import shutil
import base64
import aiohttp
import aiofiles
import json
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp

try:
    from astrbot.api.event import EventMessageType
except ImportError:
    try:
        from astrbot.api.event.filter import EventMessageType
    except ImportError:
        class EventMessageType:
            ALL = "all"


@register("stt_sensevoice", "AstrBot", "SenseVoice 语音转文字插件", "1.0.0")
class SenseVoiceSTTPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.sensevoice_url = "http://localhost:8000"
        self.temp_dir = os.path.join(os.path.dirname(__file__), "temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        logger.info(f"[SenseVoice] 插件初始化完成")

    @filter.event_message_type(EventMessageType.ALL)
    async def auto_stt(self, event: AstrMessageEvent):
        has_voice, voice_url = self._extract_voice_from_event(event)
        
        if not has_voice:
            return
        
        logger.info(f"[SenseVoice] 识别语音并送大模型...")
        
        try:
            text = await self._recognize_voice_to_text(event, voice_url)
            
            if not text:
                yield event.plain_result("语音识别失败")
                return
            
            logger.info(f"[SenseVoice] 识别结果: {text[:30]}...")
            
            func_tool_mgr = self.context.get_llm_tool_manager()
            uid = event.unified_msg_origin
            
            curr_cid = await self.context.conversation_manager.get_curr_conversation_id(uid)
            
            conversation = None
            contexts = []
            system_prompt = ""
            
            if curr_cid:
                conversation = await self.context.conversation_manager.get_conversation(uid, curr_cid)
                if conversation:
                    contexts = json.loads(conversation.history) if conversation.history else []
                    
                    persona_id = conversation.persona_id
                    
                    if not persona_id and persona_id != "[%None]":
                        persona_id = self.context.provider_manager.selected_default_persona.get("name")
                    
                    if persona_id and persona_id != "[%None]":
                        personas = self.context.provider_manager.personas
                        for p in personas:
                            if p.get("name") == persona_id or p.get("id") == persona_id:
                                system_prompt = p.get("system_prompt", "")
                                break
            
            logger.info(f"[SenseVoice] 使用人格: {persona_id or '默认'}, 历史记录: {len(contexts)}条")
            
            yield event.request_llm(
                prompt=text,
                func_tool_manager=func_tool_mgr,
                session_id=curr_cid,
                contexts=contexts,
                system_prompt=system_prompt,
                conversation=conversation
            )
            
        except Exception as e:
            logger.error(f"[SenseVoice] 处理异常: {e}", exc_info=True)
            yield event.plain_result(f"处理出错: {str(e)}")

    @filter.command("语音转文字")
    async def voice_to_text(self, event: AstrMessageEvent):
        has_voice, voice_url = self._extract_voice_from_event(event)
        
        if not has_voice:
            yield event.plain_result("请回复一条语音消息")
            return

        try:
            text = await self._recognize_voice_to_text(event, voice_url)
            
            if not text:
                yield event.plain_result("识别失败")
                return
            
            func_tool_mgr = self.context.get_llm_tool_manager()
            uid = event.unified_msg_origin
            curr_cid = await self.context.conversation_manager.get_curr_conversation_id(uid)
            
            conversation = None
            contexts = []
            system_prompt = ""
            
            if curr_cid:
                conversation = await self.context.conversation_manager.get_conversation(uid, curr_cid)
                if conversation:
                    contexts = json.loads(conversation.history) if conversation.history else []
                    persona_id = conversation.persona_id
                    if not persona_id and persona_id != "[%None]":
                        persona_id = self.context.provider_manager.selected_default_persona.get("name")
                    if persona_id and persona_id != "[%None]":
                        for p in self.context.provider_manager.personas:
                            if p.get("name") == persona_id:
                                system_prompt = p.get("system_prompt", "")
                                break
            
            yield event.request_llm(
                prompt=text,
                func_tool_manager=func_tool_mgr,
                session_id=curr_cid,
                contexts=contexts,
                system_prompt=system_prompt,
                conversation=conversation
            )
                
        except Exception as e:
            logger.error(f"[SenseVoice] 异常: {e}")
            yield event.plain_result(f"出错")

    def _extract_voice_from_event(self, event: AstrMessageEvent) -> tuple:
        for comp in event.message_obj.message:
            if isinstance(comp, Comp.Record):
                return True, comp.file
        
        for comp in event.message_obj.message:
            if isinstance(comp, Comp.Reply) and comp.message:
                for reply_comp in comp.message:
                    if isinstance(reply_comp, Comp.Record):
                        return True, reply_comp.file
        return False, None

    async def _recognize_voice_to_text(self, event: AstrMessageEvent, voice_url: str) -> str:
        voice_path = await self._get_voice_file(event, voice_url)
        if not voice_path:
            return None
        
        try:
            if voice_path.lower().endswith('.amr'):
                if not self.ffmpeg_available:
                    return None
                wav_path = voice_path.replace('.amr', '.wav')
                if await self._convert_amr_to_wav(voice_path, wav_path):
                    os.remove(voice_path)
                    voice_path = wav_path
                else:
                    return None
            
            return await self._recognize_speech(voice_path)
            
        finally:
            if os.path.exists(voice_path):
                try:
                    os.remove(voice_path)
                except:
                    pass

    async def _get_voice_file(self, event: AstrMessageEvent, voice_url: str) -> str:
        if not (voice_url.startswith("http") or voice_url.startswith("file://") or voice_url.startswith("base64://")):
            if event.get_platform_name() == "aiocqhttp":
                try:
                    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                    if isinstance(event, AiocqhttpMessageEvent):
                        result = await event.bot.api.call_action("get_record", file=voice_url, out_format="wav")
                        if result and result.get("file"):
                            dst_path = os.path.join(self.temp_dir, f"{voice_url}.wav")
                            shutil.copy2(result["file"], dst_path)
                            return dst_path
                except Exception as e:
                    logger.error(f"[SenseVoice] API获取失败: {e}")
            return None
        
        elif voice_url.startswith("http"):
            temp_path = os.path.join(self.temp_dir, f"http_{abs(hash(voice_url))}.wav")
            async with aiohttp.ClientSession() as session:
                async with session.get(voice_url, timeout=30) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(temp_path, "wb") as f:
                            await f.write(await resp.read())
                        return temp_path
            return None
        
        elif voice_url.startswith("file://"):
            path = voice_url[7:]
            return path if os.path.exists(path) else None
        
        elif voice_url.startswith("base64://"):
            temp_path = os.path.join(self.temp_dir, f"base64_{abs(hash(voice_url))}.amr")
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(base64.b64decode(voice_url[9:]))
            return temp_path
        
        return None

    async def _convert_amr_to_wav(self, amr_path: str, wav_path: str) -> bool:
        try:
            import asyncio
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", amr_path, "-ar", "16000", "-ac", "1", wav_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0 and os.path.exists(wav_path)
        except Exception as e:
            logger.error(f"[SenseVoice] 转换失败: {e}")
            return False

    async def _recognize_speech(self, audio_path: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                async with aiofiles.open(audio_path, "rb") as f:
                    data.add_field(
                        "file",
                        await f.read(),
                        filename=os.path.basename(audio_path),
                        content_type="audio/wav"
                    )

                async with session.post(
                    f"{self.sensevoice_url}/asr",
                    data=data,
                    headers={"accept": "application/json"},
                    timeout=60
                ) as resp:
                    text = await resp.text()
                    
                    if resp.status != 200:
                        logger.error(f"[SenseVoice] API 错误: {text[:200]}")
                        return None
                    
                    try:
                        result = await resp.json()
                    except:
                        return text.strip()
                    
                    if isinstance(result, dict):
                        return result.get("text") or result.get("result") or result.get("data")
                    elif isinstance(result, list):
                        return str(result[0]) if result else None
                    return str(result)
                        
        except Exception as e:
            logger.error(f"[SenseVoice] API 请求失败: {e}")
            return None
