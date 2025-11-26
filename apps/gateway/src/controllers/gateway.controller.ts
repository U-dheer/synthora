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
  Res,
  Sse,
  MessageEvent,
  UploadedFiles,
} from '@nestjs/common';
import { GatewayService } from '../services/gateway.service';
import { AskAiDto } from '../dtos/ask-ai.dto';
import { SaveChatInterceptor } from '../common/interceptors/save-chat.interceptor';
import { GatewayAuthGuard } from '../guards/gateway-auth.guard';
import { type Request, type Response } from 'express';
import { AnyFilesInterceptor } from '@nestjs/platform-express';

@Controller()
@UseGuards(GatewayAuthGuard)
export class GatewayController {
  constructor(private readonly gatewayService: GatewayService) {}

  // @Post('process')
  // @UseInterceptors(AnyFilesInterceptor())
  // async processRequest(
  //   @UploadedFiles() files: any[],
  //   @Req() req: Request,
  // ) {
  //   const hasDocumentFile = files?.some((file) =>
  //     [
  //       'application/pdf', // PDF
  //       'application/msword', // DOC
  //       'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // DOCX
  //       'text/plain', // TXT
  //     ].includes(file.mimetype),
  //   );

  //   if (hasDocumentFile) {
  //     // 👉 User uploaded pdf/doc/docx/txt → go to route A
  //     return this.handleDocumentUpload(req, files);
  //   }

  //   // 👉 No document file uploaded → route B
  //   return this.handleNormalRequest(req);
  // }

  // @Post('ask')
  // @UseInterceptors(SaveChatInterceptor)
  // async askAI(@Body() askAiDto: AskAiDto) {
  //   return this.gatewayService.handleAIRequest(askAiDto.question);
  // }

  // @Post('stream')
  // async streamAI(@Body() askAiDto: AskAiDto, @Res() res: Response) {
  //   res.setHeader('Content-Type', 'text/event-stream');
  //   res.setHeader('Cache-Control', 'no-cache');
  //   res.setHeader('Connection', 'keep-alive');
  //   res.setHeader('X-Accel-Buffering', 'no');

  //   const stream = await this.gatewayService.handleAIStreamRequest(
  //     askAiDto.question,
  //   );
  //   const reader = stream.getReader();

  //   try {
  //     while (true) {
  //       const { done, value } = await reader.read();
  //       if (done) break;
  //       res.write(value);
  //     }
  //   } catch (error) {
  //     console.error('Stream error:', error);
  //   } finally {
  //     res.end();
  //   }
  // }

  @Post('ask')
  @UseInterceptors(AnyFilesInterceptor())
  async routeAI(
    @UploadedFiles() files: any[],
    @Body() askAiDto: AskAiDto,
    @Res() res: Response,
  ) {
    const hasDocumentFile = files?.some((file) =>
      [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
      ].includes(file.mimetype),
    );

    if (hasDocumentFile) {
      // 👉 Route to streamAI logic
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('X-Accel-Buffering', 'no');

      const stream = await this.gatewayService.handleAIStreamRequest(
        askAiDto.question,
        files,
      );

      const reader = stream.getReader();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          res.write(value);
        }
      } catch (error) {
        console.error('Stream error:', error);
      } finally {
        res.end();
      }
      return;
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
