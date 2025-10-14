const express = Require("express");
const axios = Require("axios");
const bodyParser = Require("body-parser");
const cors = Require("cors");
const { Pool } = Require("pg");

const app = express();
app.use(cors());
app.use(bodyParser.json());

// ====== PostgreSQL Setup ======
const pool = new Pool({
  user: "postgres",       // your DB user
  host: "localhost",
  database: "donations",  // your DB name
  password: "password",   // your DB password
  port: 5432,
});

pool.query(`
  CREATE TABLE IF NOT EXISTS mpesa_payments (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20),
    amount NUMERIC,
    checkoutRequestID VARCHAR(50),
    status VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW()
  )
`);

// ====== M-Pesa Sandbox Credentials ======
const consumerKey = "YOUR_CONSUMER_KEY";
const consumerSecret = "YOUR_CONSUMER_SECRET";
const shortCode = "YOUR_PAYBILL_OR_TILL";
const passkey = "YOUR_PASSKEY";
const callbackURL = "https://your-public-url.ngrok.io/api/mpesa/callback"; // use ngrok

// ====== Generate Access Token ======
const getAccessToken = async () => {
  const auth = Buffer.from(`${consumerKey}:${consumerSecret}`).toString("base64");
  const { data } = await axios.get(
    "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
    { headers: { Authorization: `Basic ${auth}` } }
  );
  return data.access_token;
};

// ====== STK Push Endpoint ======
app.post("/api/mpesa/stkpush", async (req, res) => {
  const { phone, amount } = req.body;

  try {
    const token = await getAccessToken();
    const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
    const password = Buffer.from(shortCode + passkey + timestamp).toString("base64");

    const stkData = {
      BusinessShortCode: shortCode,
      Password: password,
      Timestamp: timestamp,
      TransactionType: "CustomerPayBillOnline",
      Amount: amount,
      PartyA: phone,
      PartyB: shortCode,
      PhoneNumber: phone,
      CallBackURL: callbackURL,
      AccountReference: "EPICARE",
      TransactionDesc: "Donation",
    };

    const { data } = await axios.post(
      "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
      stkData,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    await pool.query(
      "INSERT INTO mpesa_payments (phone, amount, checkoutRequestID, status) VALUES ($1, $2, $3, $4)",
      [phone, amount, data.CheckoutRequestID, "pending"]
    );

    res.json({ success: true, data });
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.json({ success: false, error: err.response?.data || err.message });
  }
});

// ====== Callback Endpoint ======
app.post("/api/mpesa/callback", async (req, res) => {
  try {
    const callbackData = req.body.Body.stkCallback;
    const checkoutRequestID = callbackData.CheckoutRequestID;
    let status = "failed";
    if (callbackData.ResultCode === 0) status = "completed";

    await pool.query(
      "UPDATE mpesa_payments SET status = $1 WHERE checkoutRequestID = $2",
      [status, checkoutRequestID]
    );

    console.log("M-Pesa Callback:", callbackData);
    res.json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: err.message });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
