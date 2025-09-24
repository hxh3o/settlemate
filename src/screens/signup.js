import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import { API } from '../api';

function SignUp() {
	let navigate = useNavigate();

	const [creds, setcreds] = useState({
		name: '',
		email: '',
		password: '',
		cnfpassword: '',
	});
	const onChange = event => {
		setcreds({ ...creds, [event.target.name]: event.target.value });
	};

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (authToken) navigate('/');
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const handleSubmit = async e => {
		e.preventDefault();
		if (creds.email.length === 0) {
			toast.error('Email is Required!', {});
			return;
		}
		if (creds.password !== creds.cnfpassword) {
			toast.error('Passwords Do Not Match!', {});
			return;
		}
        const response = await fetch(`${API}/signup`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				name: creds.name,
				email: creds.email,
                password: creds.password,
                password_confirm: creds.password,
			}),
		});
		const json = await response.json();
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
		} else {
			localStorage.setItem('authToken', json.authToken);
			localStorage.setItem('welcome', true);
			navigate('/');
		}
	};

	const login = async e => {
		e.preventDefault();
		navigate('/login');
	};

	return (
		<div style={{ width: '100%', height: '100%' }}>
			<form
				onSubmit={handleSubmit}
				style={{
					display: 'flex',
					flexDirection: 'column',
					justifyContent: 'center',
					alignItems: 'center',
					width: '100%',
					height: '100%',
				}}
			>
				<TextField
					label='Name'
					variant='outlined'
					type='text'
					id='name'
					name='name'
					value={creds.name}
					onChange={onChange}
					style={{ width: '27%' }}
				></TextField>
				<TextField
					label='Email'
					variant='outlined'
					type='text'
					id='email'
					name='email'
					value={creds.email}
					onChange={onChange}
					style={{ marginTop: '20px', width: '27%' }}
				></TextField>
				<TextField
					label='Password'
					variant='outlined'
					type='password'
					id='password'
					name='password'
					value={creds.password}
					onChange={onChange}
					style={{ marginTop: '20px', width: '27%' }}
				></TextField>
				<TextField
					label='Confirm Password'
					variant='outlined'
					type='password'
					id='cnfpassword'
					name='cnfpassword'
					value={creds.cnfpassword}
					onChange={onChange}
					style={{ marginTop: '20px', width: '27%' }}
				></TextField>
				<div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', width: '27%', height: '56px', gap: '5%' }}>
					<Button variant='contained' type='submit' style={{ width: '50%', height: '100%' }}>
						Sign Up
					</Button>
					<Button variant='outlined' style={{ width: '50%', height: '100%' }} onClick={login}>
						Login
					</Button>
				</div>
			</form>
		</div>
	);
}

export default SignUp;
