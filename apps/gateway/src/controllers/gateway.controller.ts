import {
  Controller,
  Post,
  Body,
  Req,
  Headers,
  Put,
  Get,
  Delete,
  Patch,
  UseInterceptors,
  UseGuards,
} from '@nestjs/common';
import { GatewayService } from '../services/gateway.service';
import { AskAiDto } from '../dtos/ask-ai.dto';
import { SaveChatInterceptor } from '../common/interceptors/save-chat.interceptor';
import { GatewayAuthGuard } from '../guards/gateway-auth.guard';

@Controller()
@UseGuards(GatewayAuthGuard)
export class GatewayController {
  constructor(private readonly gatewayService: GatewayService) {}

  @Post('ask')
  @UseInterceptors(SaveChatInterceptor)
  async askAI(@Body() askAiDto: AskAiDto) {
    console.log('Received askAI request:', askAiDto);
    console.log('Question:', askAiDto.question);

    if (!askAiDto.question) {
      throw new Error('Question is required');
    }

    return this.gatewayService.handleAIRequest(askAiDto.question);
  }

  // Forward all HTTP methods dynamically
  @Get('*')
  async forwardGet(@Req() req, @Headers() headers: any) {
    return this.gatewayService.forwardRequest(
      req.method,
      req.url,
      undefined,
      headers,
    );
  }

  @Post('*')
  async forwardPost(@Req() req, @Body() body: any, @Headers() headers: any) {
    // If the incoming request is multipart/form-data (file upload), pass
    // the raw request stream through so the gateway forwards the multipart
    // body and boundary correctly. For normal JSON requests, forward the
    // parsed body as before.
    const contentType = headers?.['content-type'] || headers?.['Content-Type'];
    const isMultipart =
      contentType && contentType.includes('multipart/form-data');
    const payload = isMultipart ? req : body;
    return this.gatewayService.forwardRequest(
      req.method,
      req.url,
      payload,
      headers,
    );
  }

  @Put('*')
  async forwardPut(@Req() req, @Body() body: any, @Headers() headers: any) {
    const contentType = headers?.['content-type'] || headers?.['Content-Type'];
    const isMultipart =
      contentType && contentType.includes('multipart/form-data');
    const payload = isMultipart ? req : body;
    return this.gatewayService.forwardRequest(
      req.method,
      req.url,
      payload,
      headers,
    );
  }

  @Patch('*')
  async forwardPatch(@Req() req, @Body() body: any, @Headers() headers: any) {
    const contentType = headers?.['content-type'] || headers?.['Content-Type'];
    const isMultipart =
      contentType && contentType.includes('multipart/form-data');
    const payload = isMultipart ? req : body;
    return this.gatewayService.forwardRequest(
      req.method,
      req.url,
      payload,
      headers,
    );
  }

  @Delete('*')
  async forwardDelete(@Req() req, @Headers() headers: any) {
    return this.gatewayService.forwardRequest(
      req.method,
      req.url,
      undefined,
      headers,
    );
  }
}
