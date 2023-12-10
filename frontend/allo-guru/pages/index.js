import Head from 'next/head';
import Image from 'next/image';
import React, { useState, useEffect, useRef } from 'react';

export default function Status({ serviceStatus }) {
  // State hooks for managing form input and messages
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [submitMessage, setSubmitMessage] = useState('');

  // New state hook for tracking if the logo has loaded
  const [logoLoaded, setLogoLoaded] = useState(false);

  // Refs for the input field and submit button
  const inputRef = useRef(null);
  const buttonRef = useRef(null);

  // State for storing the combined width
  const [marqueeWidth, setMarqueeWidth] = useState('auto');

  // Function to handle logo load
  const handleLogoLoad = () => {
    setLogoLoaded(true);
  };

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
      const response = await fetch('https://www.allo.guru/api/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      // Directly read and parse the JSON response
      const jsonResponse = await response.json();
      setSubmitMessage(jsonResponse.message);

    } catch (error) {
      console.error('Error submitting email:', error);
      setSubmitMessage('Error submitting email');
    }
  };

  useEffect(() => {
    const calculateWidth = () => {
      if (inputRef.current && buttonRef.current) {
        const inputWidth = inputRef.current.offsetWidth;
        const buttonWidth = buttonRef.current.offsetWidth;
        setMarqueeWidth(`${inputWidth + buttonWidth}px`);
      }
    };

    // Calculate the width on mount and window resize
    window.addEventListener('resize', calculateWidth);
    calculateWidth();

    // Cleanup the event listener
    return () => window.removeEventListener('resize', calculateWidth);
  }, []);

  return (
    <div className="container">
      <Head>
        <title>Allo Guru</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Image
        src="/logo.png"
        alt="Allo Guru Logo"
        className="logo"
        onLoadingComplete={handleLogoLoad}
        width={200} // specify width
        height={100} // specify height
        priority // to preload the image
      />

      <div className="marquee-wrapper" style={{ width: marqueeWidth }}>
        <div className="marquee-container">
          <p className="serviceMessage">{serviceStatus.message}</p>
        </div>
      </div>

      <p className="alertMessage">Sign up for email alerts</p>

      <form onSubmit={handleSubmit} className="formElement">
        <input
          ref={inputRef}
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
          className="inputField"
        />
        <button ref={buttonRef} type="submit" className="subscribeButton">Subscribe</button>
        {emailError && <p className="errorMessage">{emailError}</p>}
      </form>

      {submitMessage && <p className="formElement">{submitMessage}</p>}

      <p className="smsMessage">Send <span className="subscribe">Subscribe</span> to 417-383-2556 for SMS alerts</p>

      <footer className="footer">
        <p>Made with ❤️ in Nebraska</p>
      </footer>
    </div>
  );
}

// Function to fetch service status from the server side before rendering the page
export async function getServerSideProps() {
  const apiUrl = 'https://www.allo.guru/api/status';

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
