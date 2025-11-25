import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PromptDto } from '@synthora/dto';
import { OpenAI } from 'openai';

@Injectable()
export class HuggingFaceService {
  private defaultClient: OpenAI;

  constructor(private configService: ConfigService) {
    this.defaultClient = new OpenAI({
      baseURL: 'https://router.huggingface.co/v1',
      apiKey: this.configService.get<string>('HF_TOKEN'),
    });
  }

  /**
   * Generate a chat completion.
   * If `forwardedAuthorization` is provided (e.g. "Bearer hf_..."), it will be used
   * for this single request instead of the configured `HF_TOKEN`.
   */
  async generateCompletion(
    message: PromptDto,
    forwardedAuthorization?: string,
  ) {
    const model = this.configService.get<string>('HF_MODEL') as string;

    // If a forwarded token is provided, strip the "Bearer " prefix and create
    // a per-request client so we can call HF on behalf of the caller.
    const tokenFromHeader = forwardedAuthorization
      ? forwardedAuthorization.replace(/^Bearer\s+/i, '')
      : undefined;

    const client = tokenFromHeader
      ? new OpenAI({
          baseURL: 'https://router.huggingface.co/v1',
          apiKey: tokenFromHeader,
        })
      : this.defaultClient;

    try {
      const chatCompletion = await client.chat.completions.create({
        model,
        messages: [
          {
            content: message.input ?? message.prompt,
            role: 'user',
          },
        ],
      });

      return {
        success: true,
        message: chatCompletion.choices[0].message,
        usage: chatCompletion.usage,
      };
    } catch (error: any) {
      const status = error?.response?.status;
      const hfData = error?.response?.data;

      if (status === 403) {
        return {
          success: false,
          error: `403 Forbidden from Hugging Face. This typically means the token does not have permission to use model ${model}. Token used: ${tokenFromHeader ? 'forwarded token' : 'configured HF_TOKEN'}. Details: ${JSON.stringify(hfData)}`,
        };
      }

      if (status) {
        return {
          success: false,
          error: `Hugging Face error (status ${status}): ${JSON.stringify(hfData)}`,
        };
      }

      return {
        success: false,
        error: error?.message || 'Unknown error from Hugging Face client',
      };
    }
  }
}
