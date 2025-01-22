import Head from 'next/head'; 
import Image from 'next/image'; 
import type { BaseSyntheticEvent } from 'react';
import React, { useEffect, useState, useRef} from 'react';
/// <reference types="@types/googlemaps" />


import  SubmitButton  from '../button/SubmitButton';
import styles from '../styles/Home.module.css';

const API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string;

//dynamically load Google Maps API
const loadGoogleMapsScript = (callback: () => void) => {
  if (typeof window.google === 'object' && typeof window.google.maps === 'object') {
    callback();
  } else {
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${API_KEY}&libraries=places`;
    script.async = true; // Ensure script loads asynchronously
    document.head.append(script);
    script.addEventListener("load", callback);
    return () => script.removeEventListener("load", callback);
  }
};
//defines a react component for the opt-in form, managing various states for user input including loading, success, and error states for form submission, and coordinates for geolocation. 
const OptInForm = () => {
  const [phone, setPhone] = useState('');
  const [phoneError, setPhoneError] = useState(false);
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState(''); 
  const [stateProvince, setStateProvince] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [street_number, setStreetNumber] = useState('');
  
  const [formKey, setFormKey] = useState(0); // a key to reset the form state.

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(false);

  const addressInputRef = useRef(null);
  const [coordinates, setCoordinates] = useState({ lat: null, lng: null });

  //validates the phone number entered by the user against a specific pattern 
  useEffect(() => {
    const phonePattern = /^(\+\d{1,2}\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/; //pattern accepts country code, dashes,dots and spaces between numbers
    setPhoneError(!phonePattern.test(phone) && phone !== '');
  }, [phone]);

  /*initializes the Google Maps Places Autocomplete feature on an input field, 
  ensuring the functionality still functions whenever the formKey changes to clear the form.*/
  useEffect(() => {
    loadGoogleMapsScript(() => {
      if (addressInputRef.current) {
        initAutocomplete();
      }
    });
  }, [formKey]); 

  // clears form input fields be setting the fields to an empty string and resetting the states to false 
  const clearForm = () => {
    setPhone('');
    setAddress('');
    setCity('');
    setCountry(''); 
    setStateProvince('');
    setZipCode('');
    setStreetNumber('');
    setCoordinates({ lat: null, lng: null });
    setError(false);
    setSuccess(false);
    setPhoneError(false);
    setFormKey(prevKey => prevKey + 1); // when the form is cleared update formKey to trigger re-render and re-initialization of Autocomplete

  };
  
  //function restricts results to addresses in the US and calls the fillInAddress function whenever a place is selected from the autocomplete suggestions
  const initAutocomplete = () => {
    if (addressInputRef.current) {
      const autocomplete = new google.maps.places.Autocomplete(addressInputRef.current, {
        componentRestrictions: { country: ["us"] },
        fields: ["address_components", "geometry"],
        types: ["address"],
      });
      autocomplete.addListener("place_changed", () => fillInAddress(autocomplete));
    }
  };
  
  /* function extracts and processes specific address fields (street no, street name, city, state, country, postal code) from the selected place in the
  Google Maps Places Autocomplete widget */
  const fillInAddress = (autocomplete: any) => {
    const place = autocomplete.getPlace();
    for (const component of place.address_components) {
      const componentType = component.types[0];
      switch (componentType) {
        case "street_number": {
          setStreetNumber(`${component.long_name} ${address}`);
          break;
        }
        case "route": {
          setAddress(`${address} ${component.short_name}`);
          break;
        }
        case "locality": {
          setCity(component.long_name);
          break;
        }
        case "administrative_area_level_1": {
          setStateProvince(component.short_name);
          break;
        }
        case "country": {
          setCountry(component.long_name);
          break;
        }
        case "postal_code": {
          setZipCode(component.long_name);
          break;
        }
      }
    }
     // Extract and set coordinates 
     const latitude = place.geometry.location.lat();
     const longitude = place.geometry.location.lng();
     setCoordinates({ lat: latitude, lng: longitude });
  };

  const sendMessage = async (e: BaseSyntheticEvent) => {
    e.preventDefault();
    if (phoneError) return; //if phone error function exits early

    //otherwise sets form state, resets previous error state, and cleans the success state 
    setLoading(true);
    setError(false);
    setSuccess(false);

    //submits data (phone number and coordinates) to server 
    try {
      const res = await fetch('/api/notification/process-opt-in', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone,
          /*address,
          city,
          country,
          stateProvince,
          zipCode,*/
          coordinates: {
          lat: coordinates.lat,
          lng: coordinates.lng  
          }
        }),
      });

      const apiResponse = await res.json();
      //testing
      //console.log(apiResponse)

      if (apiResponse.success) {
        setSuccess(true);
      } else {
        setError(true); // potentially due to network issues or server errors
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setError(true);
    }

    setLoading(false);
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>Opt In Form</title>  {/* form title */}
      </Head>
      <form key={formKey} className={styles.form} onSubmit={sendMessage} autoComplete="off">
        <Image
          src="/emberalert.png" 
          width={900}
          height={200}
          alt="Ember Alert"
        />
        <h1 className={styles.title}>
          Opt in to receive SMS text messages if a wildfire is in your area!
        </h1>

        {/* Form Group for Phone Number */}
        <div className={styles.formGroup}>
          <label htmlFor="phone">Phone Number</label>
          <input
            type="tel"
            id="phone"
            name="phone"
            onChange={(e) => setPhone(e.target.value)}
            placeholder="0123456789"
            className={styles.input}
            required
            autoComplete="new-password" //to get rid of autocomplete from browser
            />
          {phoneError && (
            <span className={styles.error}>
              Please enter a valid phone number
            </span>
          )}
        </div>

        {/* Form Group for Street */}
        <div className={styles.formGroup}>
          <label htmlFor="address1Field">Address</label>
          <input
          type="text"
          className={styles.input}
          id="address1Field" 
          placeholder="1234 Main St"
          ref={addressInputRef} 
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          required
          autoComplete="new-password" //to get rid of autocomplete from browser
        />
        </div>

        {/* Form Group for Street number */}
        <div className={styles.formGroup}>
          <label htmlFor="street_number">Street Number</label>
          <input
            type="text"
            id="street_number"
            name="street_number"
            className={styles.input}
            value={street_number}
            onChange={(e) => setStreetNumber(e.target.value)}
            required
            autoComplete="new-password" //to get rid of autocomplete from browser

            />
        </div>

        {/* Form Group for City */}
        <div className={styles.formGroup}>
          <label htmlFor="locality">City</label>
          <input
            type="text"
            id="locality"
            name="locality"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
            className={styles.input}
            autoComplete="new-password" //to get rid of autocomplete from browser
          />
        </div>

        {/* Form Group for State */}
        <div className={styles.formGroup}>
          <label htmlFor="state">State</label>
          <input
            type="text"
            id="state"
            name="state"
            value={stateProvince}
            onChange={(e) => setStateProvince(e.target.value)}
            required
            className={styles.input}
            autoComplete="new-password" //to get rid of autocomplete from browser
          />
        </div>

        {/* Form Group for Postal Code */}
        <div className={styles.formGroup}>
          <label htmlFor="postcode">Postal code</label>
          <input
            type="text"
            id="postcode"
            name="postcode"
            value={zipCode}
            onChange={(e) => setZipCode(e.target.value)}
            required
            className={styles.input}
            autoComplete="new-password" //to get rid of autocomplete from browser
          />
        </div>

        {/* Form Group for Country */}
        <div className={styles.formGroup}>
          <label htmlFor="country">Country</label>
          <input
            type="text"
            id="country"
            name="country"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            required
            className={styles.input}
            autoComplete="new-password" //to get rid of autocomplete from browser

          />
        </div>

        {/* Submit Button */}
        <div style={{ display: 'flex', justifyContent: 'center'}}>
          <SubmitButton isLoading={loading} xl>
            Submit
          </SubmitButton>
        </div>
           
        {/* Clear Form Button */}
        <div style={{textAlign: 'center', justifyContent: 'center', float:'right', backgroundColor: '#e7e7e7', color: 'black', padding: '10px'}}>
          <button type="button" onClick={clearForm} className={styles.clearButton}>
            Clear Form
          </button>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <p className={styles.success}>Message sent successfully.</p>
        )}
        {error && (
          <p className={styles.error}>
            Something went wrong. Please try again.
          </p>
        )}
      </form>
    </div>
  );
};

export { OptInForm };
