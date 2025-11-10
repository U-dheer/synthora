import { IsOptional, IsArray, IsObject, IsString } from "class-validator";

export class CreateGeminiDto {
  @IsOptional()
  @IsArray()
  responses?: any[];

  @IsOptional()
  @IsObject()
  response?: any;

  @IsOptional()
  @IsString()
  input?: string;

  @IsOptional()
  @IsArray()
  messages?: any[];

  @IsOptional()
  @IsObject()
  prompt?: any;
}
