import type { NextApiRequest, NextApiResponse } from 'next';
import twilio from 'twilio';

export default function sendMessage(req: NextApiRequest, res: NextApiResponse) {
  const accountSid = <string>process.env.TWILIO_ACCOUNT_SID;
  const token = <string>process.env.TWILIO_AUTH_TOKEN;
  const client = twilio(accountSid, token);

  // Only allow POST requests for this endpoint
  if (req.method !== 'POST') {
    res.status(405).end('Method Not Allowed');
    return;
  }

  // Extract variables from the request body
  const { phone, address, city, stateProvince, zipCode, country, coordinates } = req.body;

  // Define the message body
  const messageBody = `EmberAlert: Thank you for opting in to receive alerts about wildfires. 
Location Details:
- Address: ${address}
- City: ${city}
- State/Province: ${stateProvince}
- Zip/Postal Code: ${zipCode}
- Country: ${country}
- Coordinates: ${coordinates} 
Std Msg & data rates may apply. Reply HELP for help, STOP to cancel.`;

  client.messages
    .create({
      body: messageBody,
      from: '17407626065',
      to: phone,
    })
    .then(() =>
      res.json({
        success: true,
      }),
    )
    .catch((error) => {
      console.error(error);
      res.json({
        success: false,
      });
    });
}
