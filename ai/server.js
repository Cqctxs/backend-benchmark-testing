const http = require("http");
const { createClient } = require("@supabase/supabase-js");

// Connect to your Supabase project
const SUPABASE_URL =
  process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

const server = http.createServer(async (req, res) => {
  if (req.method === "GET" && req.url === "/match") {
    const start = process.hrtime.bigint();

    try {
      // For the JMeter test, we simulate User #1 clicking "Match"
      const simulatedUserId = 1;

      // Tell Supabase to run the vector math
      const { data: matchedUsers, error } = await supabase.rpc(
        "match_users_by_id",
        {
          p_user_id: simulatedUserId,
          match_threshold: 0.8, // Only match if they are 80% similar
          match_count: 10, // Return up to 10 matches
        },
      );

      if (error) throw error;

      const end = process.hrtime.bigint();
      const durationMicros = Number(end - start) / 1000;

      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          status: "Success",
          matches_made: matchedUsers ? matchedUsers.length : 0,
          processing_time_micros: Math.round(durationMicros),
        }),
      );
    } catch (err) {
      console.error(err);
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "Error", message: err.message }));
    }
  } else {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not Found");
  }
});

const PORT = 8080;
server.listen(PORT, "0.0.0.0", () => {
  console.log(`Node.js AI matching server running on port ${PORT}...`);
});
