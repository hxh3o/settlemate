import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { API, authHeaders } from '../api';

function EditProfile() {
	let navigate = useNavigate();
	const [creds, setcreds] = useState({ name: '', email: '', upi: '' });
	const onChange = event => {
		setcreds({ ...creds, [event.target.name]: event.target.value });
	};

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (!authToken) navigate('/');
			else fetchData();
		}
		async function fetchData() {
			try {
                const response = await fetch(`${API}/getUserData`, {
                    method: 'GET',
                    headers: authHeaders(),
                });
				const json = await response.json();
				if (!json.success) {
					json.errors.forEach(error => {
						toast.error(error.msg, {});
					});
					if (json.logout === true) navigate('/');
				} else {
					const temp = {
						name: json.data.name,
						email: json.data.email,
						upi: json.data.upi,
					};
					setcreds(temp);
					// console.log(json.data);
					if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
				}
			} catch (error) {
				console.error('Error fetching data :', error);
			}
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const handleSubmit = async e => {
		e.preventDefault();
        const response = await fetch(`${API}/editprofile`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                name: creds.name,
                upi: creds.upi,
            }),
        });
		const json = await response.json();
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
			navigate('/profile');
		}
	};

	return (
		<div
			style={{
				display: 'flex',
				justifyContent: 'center',
				alignItems: 'center',
				height: '100vh',
			}}
		>
			<form onSubmit={handleSubmit}>
				<label htmlFor='name'>Name:</label>
				<input type='text' id='name' name='name' required value={creds.name} onChange={onChange}></input>
				<label htmlFor='email'>Email:</label>
				<input type='text' id='email' name='email' required value={creds.email} onChange={onChange} disabled></input>
				<label htmlFor='upi'>UPI:</label>
				<input type='text' id='upi' name='upi' value={creds.upi} onChange={onChange}></input>
				<button type='submit'>Save</button>
			</form>
		</div>
	);
}

export default EditProfile;
