// Import necessary React and Next.js components
import Head from 'next/head';
import React, { useState } from 'react';

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

  return (
    <div className="container">
      <Head>
        <title>Allo Guru</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <img src="/logo.png" alt="Allo Guru Logo" className="logo" />

      <div className="marquee-wrapper">
        <div className="marquee-container">
          <p className="serviceMessage">{serviceStatus.message}</p>
        </div>
      </div>

      <p className="alertMessage">Sign up for email alerts!</p>

      <form onSubmit={handleSubmit} className="formElement">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
          className="inputField"
        />
        <button type="submit" className="subscribeButton">Subscribe</button>
        {emailError && <p className="errorMessage">{emailError}</p>}
      </form>

      {submitMessage && <p className="formElement">{submitMessage}</p>}

      <p className="smsMessage">Sign up for sms alerts @ 417-383-2556</p>

      <footer className="footer">
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
