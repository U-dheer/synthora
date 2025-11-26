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

  async generateCompletion(message: PromptDto) {
    const model = this.configService.get<string>('HF_MODEL') as string;

    const client = this.defaultClient;
    try {
      const chatCompletion = await client.chat.completions.create({
        model,
        messages: [
          {
            content: message.input ?? message.prompt ?? '',
            role: 'user',
          },
          {
            role: 'system',
            content: message.context ?? '',
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
