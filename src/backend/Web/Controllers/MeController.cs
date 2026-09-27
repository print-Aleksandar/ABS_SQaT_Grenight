using System.Security.Claims;
using Domain.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;

namespace Web.Controllers;

[ApiController]
[Route("api/me")]
[Authorize]
public class MeController : ControllerBase
{
    private readonly UserManager<Player> _userManager;

    public MeController(UserManager<Player> userManager)
    {
        _userManager = userManager;
    }

    [HttpGet]
    public async Task<IActionResult> Get()
    {
        var playerId = Guid.Parse(User.FindFirst(ClaimTypes.NameIdentifier)!.Value);
        var player = await _userManager.FindByIdAsync(playerId.ToString());
        if (player == null)
        {
            return NotFound(new { error = $"[MeController.Get] Player not found. playerId={playerId}" });
        }

        return Ok(new
        {
            id = player.Id,
            username = player.UserName,
            email = player.Email,
            points = player.Points,
            isOnline = player.IsOnline,
            isInGame = player.IsInGame,
            registeredAt = player.Timestamp,
            lastSeenAt = player.LastSeen,
            profilePictureUrl = player.ProfilePictureUrl
        });
    }
}