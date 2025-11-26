import { IsOptional, IsArray, IsObject, IsString } from "class-validator";

export class PromptDto {
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
  @IsString()
  prompt?: string;

  @IsString()
  context?: string;
}
