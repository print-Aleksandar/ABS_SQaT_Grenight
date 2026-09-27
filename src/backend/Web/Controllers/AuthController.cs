using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Domain.Models;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.IdentityModel.Tokens;

namespace Web.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly UserManager<Player> _userManager;
    private readonly IConfiguration _config;

    public AuthController(UserManager<Player> userManager, IConfiguration config)
    {
        _userManager = userManager;
        _config = config;
    }

    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] RegisterDto dto)
    {
        if (string.IsNullOrWhiteSpace(dto.Username) || string.IsNullOrWhiteSpace(dto.Email) || string.IsNullOrWhiteSpace(dto.Password))
        {
            return BadRequest(new { error = "[AuthController.Register] Username, email, and password are required." });
        }

        var existing = await _userManager.FindByEmailAsync(dto.Email);
        if (existing != null)
        {
            return Conflict(new { error = $"[AuthController.Register] Email already registered. email={dto.Email}" });
        }

        var player = new Player
        {
            UserName = dto.Username,
            Email = dto.Email,
            IsOnline = true,
            LastSeen = DateTime.UtcNow
        };

        var result = await _userManager.CreateAsync(player, dto.Password);
        if (!result.Succeeded)
        {
            var errors = string.Join("; ", result.Errors.Select(e => e.Description));
            return BadRequest(new { error = $"[AuthController.Register] Identity rejected registration. errors={errors}" });
        }

        return Ok(IssueToken(player));
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginDto dto)
    {
        var player = await _userManager.FindByEmailAsync(dto.Email);
        if (player == null)
        {
            return Unauthorized(new { error = $"[AuthController.Login] Invalid credentials. email={dto.Email}" });
        }

        var passwordOk = await _userManager.CheckPasswordAsync(player, dto.Password);
        if (!passwordOk)
        {
            return Unauthorized(new { error = $"[AuthController.Login] Invalid credentials. email={dto.Email}" });
        }

        player.IsOnline = true;
        await _userManager.UpdateAsync(player);

        return Ok(IssueToken(player));
    }

    private object IssueToken(Player player)
    {
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
        var lifetimeMinutes = int.Parse(_config["Jwt:PlatformTokenLifetimeMinutes"]!);

        var claims = new List<Claim>
        {
            new Claim(JwtRegisteredClaimNames.Sub, player.Id.ToString()),
            new Claim(ClaimTypes.NameIdentifier, player.Id.ToString()),
            new Claim(ClaimTypes.Name, player.UserName ?? ""),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
        };

        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: DateTime.UtcNow.AddMinutes(lifetimeMinutes),
            signingCredentials: creds
        );

        return new
        {
            accessToken = new JwtSecurityTokenHandler().WriteToken(token),
            expiresInMinutes = lifetimeMinutes,
            playerId = player.Id,
            username = player.UserName,
        };
    }
}