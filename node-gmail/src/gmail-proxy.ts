import express, { Request, Response } from "express";
import cors from "cors";
import { google, gmail_v1 } from "googleapis";
import { OAuth2Client } from "google-auth-library";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const CLIENT_ID = process.env.GOOGLE_CLIENT_ID || "";
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || "";
const REDIRECT_URI = process.env.GOOGLE_REDIRECT_URI || "http://localhost:3000/auth/google/callback";

let oauth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);
let gmail: gmail_v1.Gmail;

function ensureAuthenticated(req: Request, res: Response, next: Function) {
  if (!gmail) {
    return res.status(401).json({ error: "Not authenticated. Visit /auth/google first." });
  }
  next();
}

app.get("/auth/google/url", (_req: Request, res: Response) => {
  const url = oauth2Client.generateAuthUrl({
    access_type: "offline",
    scope: [
      "https://www.googleapis.com/auth/gmail.readonly",
      "https://www.googleapis.com/auth/gmail.send",
      "https://www.googleapis.com/auth/gmail.modify",
    ],
  });
  res.json({ authUrl: url });
});

app.get("/auth/google/callback", async (req: Request, res: Response) => {
  const { code } = req.query;
  if (!code) return res.status(400).json({ error: "Missing code" });

  const { tokens } = await oauth2Client.getToken(code as string);
  oauth2Client.setCredentials(tokens);
  gmail = google.gmail({ version: "v1", auth: oauth2Client });
  res.json({ success: true, message: "Authenticated" });
});

app.get("/messages", ensureAuthenticated, async (req: Request, res: Response) => {
  const maxResults = parseInt(req.query.maxResults as string) || 50;
  const q = req.query.q as string;

  const list = await gmail.users.messages.list({ userId: "me", maxResults, q });
  const messages = list.data.messages || [];
  res.json(messages);
});

app.get("/messages/:id", ensureAuthenticated, async (req: Request, res: Response) => {
  const msg = await gmail.users.messages.get({ userId: "me", id: req.params.id, format: "full" });
  res.json(msg.data);
});

app.get("/threads/:id", ensureAuthenticated, async (req: Request, res: Response) => {
  const thread = await gmail.users.threads.get({ userId: "me", id: req.params.id });
  res.json(thread.data);
});

app.post("/send", ensureAuthenticated, async (req: Request, res: Response) => {
  const { to, subject, body, threadId } = req.body;
  const headers = [
    "To: " + to,
    "Subject: " + subject,
    "Content-Type: text/plain; charset=UTF-8",
  ];
  if (threadId) {
    headers.push("In-Reply-To: " + threadId);
  }
  const message = headers.join("\n") + "\n\n" + body;
  const encoded = Buffer.from(message).toString("base64url");

  const sent = await gmail.users.messages.send({
    userId: "me",
    requestBody: { raw: encoded, threadId },
  });
  res.json({ messageId: sent.data.id });
});

const PORT = parseInt(process.env.NODE_PORT || "3000");
app.listen(PORT, () => {
  console.log(`Gmail proxy running on port ${PORT}`);
});