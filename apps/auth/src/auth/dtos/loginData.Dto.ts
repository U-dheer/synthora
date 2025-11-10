import { IsEmail, IsString } from 'class-validator';

export class loginDataDto {
  @IsEmail()
  email: string;

  @IsString()
  password: string;
}
