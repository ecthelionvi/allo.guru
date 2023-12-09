// Import necessary React and Next.js components
import React, { useState } from 'react';
import Head from 'next/head';

// Define the main component, Status, which takes 'serviceStatus' as a prop
export default function Status({ serviceStatus }) {
  // State hooks for managing form input and messages
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [submitMessage, setSubmitMessage] = useState('');

  // Function to handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default form submission behavior

    // Regular expression for validating email format
    const re = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    if (!re.test(email)) {
      setEmailError('Invalid email address');
      return;
    }
    setEmailError('');

    // Prepare form data for submission
    const formData = new URLSearchParams();
    formData.append('email', email);

    try {
      // Send a POST request to the subscribe API endpoint
      const response = await fetch('https://0.0.0.0:8000/api/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      // Read and set the response message
      const message = await response.text();
      setSubmitMessage(message);
    } catch (error) {
      console.error('Error submitting email:', error);
      setSubmitMessage('Error submitting email.');
    }
  };

  // Style object for consistent element spacing
  const elementStyle = { margin: '12px 0' };

  // JSX for rendering the component
  return (
    <div style={{ fontFamily: 'Helvetica', margin: '0 auto', maxWidth: '550px', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '10px' }}>
      <Head>
        <title>Allo Guru</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <h1 style={elementStyle}>Allo Guru</h1>
      <p style={elementStyle}>{serviceStatus.message}</p>

      <p style={{ fontSize: '18px', fontWeight: 'bold' }}>Sign up for email alerts!</p>

      <form onSubmit={handleSubmit} style={{ ...elementStyle, width: '55%', display: 'flex', alignItems: 'center' }}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
          style={{ flex: 1, marginRight: '10px' }}
        />
        <button type="submit" style={{ flexShrink: 0 }}>Subscribe</button>
        {emailError && <p style={{ color: 'red', margin: '10px 0', width: '100%' }}>{emailError}</p>}
      </form>

      {submitMessage && <p style={elementStyle}>{submitMessage}</p>}

      <div className="sms_message" style={{ backgroundColor: 'black', color: 'white', padding: '2px 4px', marginTop: '12px' }}>
        <code>send "subscribe" to (417) 383 2556 for SMS Alerts</code>
      </div>

      <footer style={elementStyle}>
        <p>Made with ❤️ in Nebraska</p>
      </footer>
    </div>
  );
}

// Function to fetch service status from the server side before rendering the page
export async function getServerSideProps() {
  const apiUrl = 'http://0.0.0.0:8000/api/status';

  try {
    // Fetch the service status from the API
    const res = await fetch(apiUrl);
    const serviceStatus = await res.json(); // Parse the JSON response

    // Return the fetched status as a prop
    return { props: { serviceStatus } };
  } catch (error) {
    console.error('Failed to fetch service status:', error);
    // Return a default error message if the fetch fails
    return { props: { serviceStatus: { message: 'Unable to fetch service status', status_code: 500 } } };
  }
}
