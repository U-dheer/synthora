import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  Put,
  UseGuards,
} from '@nestjs/common';
import { AuthService } from './auth.service';
import { signUpDataDto } from './dtos/signUpData.Dto';
import { loginDataDto } from './dtos/loginData.Dto';
import { RefreshTokenDto } from './dtos/refreshToken.dto';
import { ChangePasswordDto } from './dtos/chnage-password.dto';
import { AuthGuard } from 'src/guards/auth.guard';
import { RequestUser } from 'src/decorators/request-user.decorator';
import { ForgotPasswordDto } from './dtos/forgot-password.sto';
import { ResetPasswordDto } from './dtos/reset-password.dto';
import { post } from 'axios';
import { ApiBody } from '@nestjs/swagger';

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('signup')
  async signUp(@Body() signUpData: signUpDataDto) {
    return this.authService.signUp(signUpData);
  }

  @ApiBody({ type: loginDataDto })
  @Post('login')
  async login(@Body() Credentials: loginDataDto) {
    return this.authService.login(Credentials);
  }

  @Post('refresh')
  async refreshTokens(@Body() refreshTokenDto: RefreshTokenDto) {
    return this.authService.refreshTokens(refreshTokenDto.refreshToken);
  }

  @Put('change-password')
  @UseGuards(AuthGuard)
  async changePassword(
    @Body() changePasswordDto: ChangePasswordDto,
    @RequestUser() userId: string,
  ) {
    return this.authService.changePassword(
      userId,
      changePasswordDto.oldPassword,
      changePasswordDto.newPassword,
    );
  }

  @Post('forgot-password')
  async forgotPassword(@Body() forgotPasswordDto: ForgotPasswordDto) {
    return this.authService.forgotPassword(forgotPasswordDto.email);
  }

  @Put('reset-password')
  async resetPassword(@Body() resetPasswordDto: ResetPasswordDto) {
    return this.authService.resetPassword(
      resetPasswordDto.newPassword,
      resetPasswordDto.resetToken,
    );
  }

  @Post('validate')
  async validateToken(@Body() tokenDto: { token: string }) {
    return this.authService.validateToken(tokenDto.token);
  }

  @Get('me')
  @UseGuards(AuthGuard)
  async me(@RequestUser() userId: string) {
    return this.authService.getMe(userId);
  }
}
