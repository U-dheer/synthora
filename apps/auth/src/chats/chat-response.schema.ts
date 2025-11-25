import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import mongoose from 'mongoose';
import type { Document } from 'mongoose';

@Schema({ timestamps: true })
export class ChatResponse {
  @Prop({ required: true, type: mongoose.Types.ObjectId, index: true })
  userId: string;

  @Prop({ type: String, required: false })
  sessionId?: string;

  // Stored summary produced by the summarizer (or fallback LLM)
  @Prop({ type: Object, required: true })
  summary: { result: string };

  // Raw responses from each AI provider. Stored in compact form to avoid
  // saving provider telemetry. Example: { ai1: { success: true, response: '...' } }
  @Prop({ type: Object, required: true })
  rawResponses: Record<string, { success: boolean; response: string }>;

  @Prop({ type: String, required: false })
  conversationId?: string;
}

export const ChatResponseSchema = SchemaFactory.createForClass(ChatResponse);
export type ChatResponseDocument = ChatResponse & Document;
