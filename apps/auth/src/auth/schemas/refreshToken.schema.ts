import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import mongoose from 'mongoose';
import type { Document } from 'mongoose';

@Schema({ versionKey: false, timestamps: true })
export class RefreshToken {
  @Prop({ required: true })
  token: string;
  @Prop({ required: true, type: mongoose.Types.ObjectId })
  userId: string;
  @Prop({ required: true })
  expiryDate: Date;
}
export const RefreshTokenSchema = SchemaFactory.createForClass(RefreshToken);
export type RefreshTokenDocument = RefreshToken & Document;
