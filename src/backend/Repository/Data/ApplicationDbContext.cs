using Domain.Models;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace Repository.Data
{
    public class ApplicationDbContext : IdentityDbContext<Player, IdentityRole<Guid>, Guid>
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options) { }

        public DbSet<FriendshipRequest> FriendshipRequests { get; set; }
        public DbSet<Friendship> Friendships { get; set; }
        public DbSet<Block> Blocks { get; set; }
        public DbSet<GameRequest> GameRequests { get; set; }
        public DbSet<Game> Games { get; set; }
        public DbSet<Piece> Pieces { get; set; }
        public DbSet<ApiRequest> ApiRequests { get; set; }
        public DbSet<ApiResponse> ApiResponses { get; set; }

        protected override void OnModelCreating(ModelBuilder builder)
        {
            base.OnModelCreating(builder);

            builder.Entity<Player>().ToTable("PLAYER");
            builder.Entity<FriendshipRequest>().ToTable("FRIENDSHIP_REQUEST");
            builder.Entity<Friendship>().ToTable("FRIENDSHIP");
            builder.Entity<Block>().ToTable("BLOCK");
            builder.Entity<GameRequest>().ToTable("GAME_REQUEST");
            builder.Entity<Game>().ToTable("GAME");
            builder.Entity<Piece>().ToTable("PIECE");
            builder.Entity<ApiRequest>().ToTable("API_REQUEST");
            builder.Entity<ApiResponse>().ToTable("API_RESPONSE");
            
            builder.Entity<Friendship>(e =>
            {
                e.Property(f => f.Friend1Id).HasColumnName("friend1_id");
                e.Property(f => f.Friend2Id).HasColumnName("friend2_id");
            });

            builder.Entity<Piece>()
                .HasKey(p => new { p.GameId, p.PieceUid });

            builder.Entity<ApiRequest>()
                .HasOne(a => a.Piece)
                .WithMany()
                .HasForeignKey(a => new { a.GameId, a.PieceUid });

            builder.Entity<Friendship>()
                .HasOne(f => f.Friend1)
                .WithMany()
                .HasForeignKey(f => f.Friend1Id)
                .OnDelete(DeleteBehavior.Restrict);
            
            builder.Entity<Friendship>()
                .HasOne(f => f.Friend2)
                .WithMany()
                .HasForeignKey(f => f.Friend2Id)
                .OnDelete(DeleteBehavior.Restrict);

            builder.Entity<FriendshipRequest>()
                .HasOne(fr => fr.Requester)
                .WithMany(p => p.SentFriendRequests)
                .HasForeignKey(fr => fr.RequesterId)
                .OnDelete(DeleteBehavior.Restrict);

            builder.Entity<FriendshipRequest>()
                .HasOne(fr => fr.Receiver)
                .WithMany(p => p.ReceivedFriendRequests)
                .HasForeignKey(fr => fr.ReceiverId)
                .OnDelete(DeleteBehavior.Restrict);

            builder.Entity<Block>()
                .HasOne(b => b.Blocker)
                .WithMany(p => p.BlockedUsers)
                .HasForeignKey(b => b.BlockerId)
                .OnDelete(DeleteBehavior.Restrict);

            builder.Entity<Block>()
                .HasOne(b => b.Blocked)
                .WithMany(p => p.BlockedByUsers)
                .HasForeignKey(b => b.BlockedId)
                .OnDelete(DeleteBehavior.Restrict);
        }
    }
}