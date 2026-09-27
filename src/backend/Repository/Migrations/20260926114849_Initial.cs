using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace Repository.Migrations
{
    /// <inheritdoc />
    public partial class Initial : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "AspNetRoles",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    name = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: true),
                    normalized_name = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: true),
                    concurrency_stamp = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_asp_net_roles", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "PLAYER",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    timestamp = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    points = table.Column<int>(type: "integer", nullable: false),
                    user_name = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: true),
                    normalized_user_name = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: true),
                    email = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: true),
                    normalized_email = table.Column<string>(type: "character varying(256)", maxLength: 256, nullable: true),
                    email_confirmed = table.Column<bool>(type: "boolean", nullable: false),
                    password_hash = table.Column<string>(type: "text", nullable: true),
                    security_stamp = table.Column<string>(type: "text", nullable: true),
                    concurrency_stamp = table.Column<string>(type: "text", nullable: true),
                    phone_number = table.Column<string>(type: "text", nullable: true),
                    phone_number_confirmed = table.Column<bool>(type: "boolean", nullable: false),
                    two_factor_enabled = table.Column<bool>(type: "boolean", nullable: false),
                    lockout_end = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true),
                    lockout_enabled = table.Column<bool>(type: "boolean", nullable: false),
                    access_failed_count = table.Column<int>(type: "integer", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_player", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "AspNetRoleClaims",
                columns: table => new
                {
                    id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    role_id = table.Column<Guid>(type: "uuid", nullable: false),
                    claim_type = table.Column<string>(type: "text", nullable: true),
                    claim_value = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_asp_net_role_claims", x => x.id);
                    table.ForeignKey(
                        name: "fk_asp_net_role_claims_asp_net_roles_role_id",
                        column: x => x.role_id,
                        principalTable: "AspNetRoles",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AspNetUserClaims",
                columns: table => new
                {
                    id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    claim_type = table.Column<string>(type: "text", nullable: true),
                    claim_value = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_asp_net_user_claims", x => x.id);
                    table.ForeignKey(
                        name: "fk_asp_net_user_claims_asp_net_users_user_id",
                        column: x => x.user_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AspNetUserLogins",
                columns: table => new
                {
                    login_provider = table.Column<string>(type: "text", nullable: false),
                    provider_key = table.Column<string>(type: "text", nullable: false),
                    provider_display_name = table.Column<string>(type: "text", nullable: true),
                    user_id = table.Column<Guid>(type: "uuid", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_asp_net_user_logins", x => new { x.login_provider, x.provider_key });
                    table.ForeignKey(
                        name: "fk_asp_net_user_logins_asp_net_users_user_id",
                        column: x => x.user_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AspNetUserRoles",
                columns: table => new
                {
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    role_id = table.Column<Guid>(type: "uuid", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_asp_net_user_roles", x => new { x.user_id, x.role_id });
                    table.ForeignKey(
                        name: "fk_asp_net_user_roles_asp_net_roles_role_id",
                        column: x => x.role_id,
                        principalTable: "AspNetRoles",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "fk_asp_net_user_roles_asp_net_users_user_id",
                        column: x => x.user_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AspNetUserTokens",
                columns: table => new
                {
                    user_id = table.Column<Guid>(type: "uuid", nullable: false),
                    login_provider = table.Column<string>(type: "text", nullable: false),
                    name = table.Column<string>(type: "text", nullable: false),
                    value = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_asp_net_user_tokens", x => new { x.user_id, x.login_provider, x.name });
                    table.ForeignKey(
                        name: "fk_asp_net_user_tokens_asp_net_users_user_id",
                        column: x => x.user_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "BLOCK",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    blocker_id = table.Column<Guid>(type: "uuid", nullable: false),
                    blocked_id = table.Column<Guid>(type: "uuid", nullable: false),
                    start_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    end_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_block", x => x.id);
                    table.ForeignKey(
                        name: "fk_block_player_blocked_id",
                        column: x => x.blocked_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "fk_block_player_blocker_id",
                        column: x => x.blocker_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "FRIENDSHIP",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    friend1_id = table.Column<Guid>(type: "uuid", nullable: false),
                    friend2_id = table.Column<Guid>(type: "uuid", nullable: false),
                    start_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    end_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_friendship", x => x.id);
                    table.ForeignKey(
                        name: "fk_friendship_player_friend1id",
                        column: x => x.friend1_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "fk_friendship_player_friend2id",
                        column: x => x.friend2_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "FRIENDSHIP_REQUEST",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    requester_id = table.Column<Guid>(type: "uuid", nullable: false),
                    receiver_id = table.Column<Guid>(type: "uuid", nullable: false),
                    request_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    decision_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    is_accepted = table.Column<bool>(type: "boolean", nullable: true),
                    start_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    end_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_friendship_request", x => x.id);
                    table.ForeignKey(
                        name: "fk_friendship_request_player_receiver_id",
                        column: x => x.receiver_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "fk_friendship_request_player_requester_id",
                        column: x => x.requester_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "GAME_REQUEST",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    requester_id = table.Column<Guid>(type: "uuid", nullable: false),
                    requested_id = table.Column<Guid>(type: "uuid", nullable: true),
                    is_accepted = table.Column<bool>(type: "boolean", nullable: true),
                    is_pvp_request = table.Column<bool>(type: "boolean", nullable: false),
                    start_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    end_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_game_request", x => x.id);
                    table.ForeignKey(
                        name: "fk_game_request_player_requested_id",
                        column: x => x.requested_id,
                        principalTable: "PLAYER",
                        principalColumn: "id");
                    table.ForeignKey(
                        name: "fk_game_request_player_requester_id",
                        column: x => x.requester_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "GAME",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    is_white_on_turn = table.Column<bool>(type: "boolean", nullable: false),
                    game_request_id = table.Column<Guid>(type: "uuid", nullable: true),
                    is_pvp = table.Column<bool>(type: "boolean", nullable: false),
                    is_draw = table.Column<bool>(type: "boolean", nullable: true),
                    is_white_winner = table.Column<bool>(type: "boolean", nullable: true),
                    start_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    end_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_game", x => x.id);
                    table.ForeignKey(
                        name: "fk_game_game_request_game_request_id",
                        column: x => x.game_request_id,
                        principalTable: "GAME_REQUEST",
                        principalColumn: "id");
                });

            migrationBuilder.CreateTable(
                name: "PIECE",
                columns: table => new
                {
                    game_id = table.Column<Guid>(type: "uuid", nullable: false),
                    piece_uid = table.Column<string>(type: "character varying(5)", maxLength: 5, nullable: false),
                    is_white = table.Column<bool>(type: "boolean", nullable: false),
                    piece_type = table.Column<short>(type: "smallint", nullable: false),
                    x = table.Column<short>(type: "smallint", nullable: false),
                    y = table.Column<short>(type: "smallint", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_piece", x => new { x.game_id, x.piece_uid });
                    table.ForeignKey(
                        name: "fk_piece_game_game_id",
                        column: x => x.game_id,
                        principalTable: "GAME",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "API_REQUEST",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    game_id = table.Column<Guid>(type: "uuid", nullable: false),
                    request_ts = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    from_player_id = table.Column<Guid>(type: "uuid", nullable: false),
                    piece_uid = table.Column<string>(type: "character varying(5)", maxLength: 5, nullable: false),
                    x = table.Column<short>(type: "smallint", nullable: false),
                    y = table.Column<short>(type: "smallint", nullable: false),
                    timestamp = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_api_request", x => x.id);
                    table.ForeignKey(
                        name: "fk_api_request_game_game_id",
                        column: x => x.game_id,
                        principalTable: "GAME",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "fk_api_request_piece_game_id_piece_uid",
                        columns: x => new { x.game_id, x.piece_uid },
                        principalTable: "PIECE",
                        principalColumns: new[] { "game_id", "piece_uid" },
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "fk_api_request_player_from_player_id",
                        column: x => x.from_player_id,
                        principalTable: "PLAYER",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "API_RESPONSE",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false),
                    api_request_id = table.Column<Guid>(type: "uuid", nullable: false),
                    status = table.Column<string>(type: "text", nullable: false),
                    message = table.Column<string>(type: "text", nullable: false),
                    timestamp = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_api_response", x => x.id);
                    table.ForeignKey(
                        name: "fk_api_response_api_request_api_request_id",
                        column: x => x.api_request_id,
                        principalTable: "API_REQUEST",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "ix_api_request_from_player_id",
                table: "API_REQUEST",
                column: "from_player_id");

            migrationBuilder.CreateIndex(
                name: "ix_api_request_game_id_piece_uid",
                table: "API_REQUEST",
                columns: new[] { "game_id", "piece_uid" });

            migrationBuilder.CreateIndex(
                name: "ix_api_response_api_request_id",
                table: "API_RESPONSE",
                column: "api_request_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "ix_asp_net_role_claims_role_id",
                table: "AspNetRoleClaims",
                column: "role_id");

            migrationBuilder.CreateIndex(
                name: "RoleNameIndex",
                table: "AspNetRoles",
                column: "normalized_name",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "ix_asp_net_user_claims_user_id",
                table: "AspNetUserClaims",
                column: "user_id");

            migrationBuilder.CreateIndex(
                name: "ix_asp_net_user_logins_user_id",
                table: "AspNetUserLogins",
                column: "user_id");

            migrationBuilder.CreateIndex(
                name: "ix_asp_net_user_roles_role_id",
                table: "AspNetUserRoles",
                column: "role_id");

            migrationBuilder.CreateIndex(
                name: "ix_block_blocked_id",
                table: "BLOCK",
                column: "blocked_id");

            migrationBuilder.CreateIndex(
                name: "ix_block_blocker_id",
                table: "BLOCK",
                column: "blocker_id");

            migrationBuilder.CreateIndex(
                name: "ix_friendship_friend1id",
                table: "FRIENDSHIP",
                column: "friend1_id");

            migrationBuilder.CreateIndex(
                name: "ix_friendship_friend2id",
                table: "FRIENDSHIP",
                column: "friend2_id");

            migrationBuilder.CreateIndex(
                name: "ix_friendship_request_receiver_id",
                table: "FRIENDSHIP_REQUEST",
                column: "receiver_id");

            migrationBuilder.CreateIndex(
                name: "ix_friendship_request_requester_id",
                table: "FRIENDSHIP_REQUEST",
                column: "requester_id");

            migrationBuilder.CreateIndex(
                name: "ix_game_game_request_id",
                table: "GAME",
                column: "game_request_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "ix_game_request_requested_id",
                table: "GAME_REQUEST",
                column: "requested_id");

            migrationBuilder.CreateIndex(
                name: "ix_game_request_requester_id",
                table: "GAME_REQUEST",
                column: "requester_id");

            migrationBuilder.CreateIndex(
                name: "EmailIndex",
                table: "PLAYER",
                column: "normalized_email");

            migrationBuilder.CreateIndex(
                name: "UserNameIndex",
                table: "PLAYER",
                column: "normalized_user_name",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "API_RESPONSE");

            migrationBuilder.DropTable(
                name: "AspNetRoleClaims");

            migrationBuilder.DropTable(
                name: "AspNetUserClaims");

            migrationBuilder.DropTable(
                name: "AspNetUserLogins");

            migrationBuilder.DropTable(
                name: "AspNetUserRoles");

            migrationBuilder.DropTable(
                name: "AspNetUserTokens");

            migrationBuilder.DropTable(
                name: "BLOCK");

            migrationBuilder.DropTable(
                name: "FRIENDSHIP");

            migrationBuilder.DropTable(
                name: "FRIENDSHIP_REQUEST");

            migrationBuilder.DropTable(
                name: "API_REQUEST");

            migrationBuilder.DropTable(
                name: "AspNetRoles");

            migrationBuilder.DropTable(
                name: "PIECE");

            migrationBuilder.DropTable(
                name: "GAME");

            migrationBuilder.DropTable(
                name: "GAME_REQUEST");

            migrationBuilder.DropTable(
                name: "PLAYER");
        }
    }
}
