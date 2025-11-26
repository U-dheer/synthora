import {
  IsArray,
  IsBoolean,
  IsNotEmpty,
  IsObject,
  IsOptional,
  IsString,
  ValidateNested,
} from 'class-validator';
import { Type } from 'class-transformer';

export class SummaryDto {
  @IsNotEmpty()
  @IsString()
  result: string;
}

export class PartDto {
  @IsNotEmpty()
  @IsString()
  text: string;
}

export class CandidateContentDto {
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => PartDto)
  parts: PartDto[];
}

export class CandidateDto {
  @IsOptional()
  @ValidateNested()
  @Type(() => CandidateContentDto)
  content?: CandidateContentDto;
}

export class RawResponseDto {
  @IsNotEmpty()
  @IsBoolean()
  success: boolean;

  @IsNotEmpty()
  @IsString()
  response: string;

  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CandidateDto)
  candidates?: CandidateDto[];
}

export class CreateChatResponseDto {
  @IsNotEmpty()
  @ValidateNested()
  @Type(() => SummaryDto)
  summary: SummaryDto;

  @IsNotEmpty()
  @IsObject()
  // Accept any provider-specific fields inside each raw response to avoid
  // strict nested validation failures (the gateway forwards varied provider
  // shapes which may include telemetry fields we don't want to persist).
  rawResponses: Record<string, any>;

  @IsOptional()
  @IsString()
  conversationId?: string;
}

export type ChatResponseDbModel = {
  summary: {
    result: string;
  };
  rawResponses: {
    [aiName: string]: {
      success: boolean;
      response: string;
    };
  };
  conversationId?: string;
};
