import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import TransactionTable from './transactionTable';

import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Typography from '@mui/material/Typography';
import { API, authHeaders } from '../api';
import Box from '@mui/material/Box';
import Modal from '@mui/material/Modal';

const style = {
	position: 'absolute',
	top: '50%',
	left: '50%',
	transform: 'translate(-50%, -50%)',
	width: 'auto',
	bgcolor: 'background.paper',
	border: '2px solid #000',
	boxShadow: 24,
	p: 4,
};

function Login() {
	let navigate = useNavigate();
	let location = useLocation();
	const [open, setOpen] = React.useState(false);
	const handleOpen = () => setOpen(true);
	const handleClose = () => setOpen(false);
	const [transactionName, setTransactionName] = useState('');
    const [amount, setAmount] = useState('');
    const [members, setMembers] = useState([]);
    const [selectedMembers, setSelectedMembers] = useState([]);

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (!authToken) navigate('/profile');
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

    useEffect(() => {
        async function loadMembers() {
            try {
                const response = await fetch(`${API}/getTripMembers`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({ tripid: location.state.tripid }),
                });
                const json = await response.json();
                if (json.success) {
                    setMembers(json.data.members || []);
                    setSelectedMembers((json.data.members || []).map(m => m._id));
                }
            } catch (e) {
                // ignore
            }
        }
        if (open) loadMembers();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open]);

    const toggleMember = id => {
        setSelectedMembers(prev => {
            const set = new Set(prev);
            if (set.has(id)) set.delete(id);
            else set.add(id);
            return Array.from(set);
        });
    };

    const submitTransactionForm = async e => {
		e.preventDefault();
    const amt = parseFloat(amount || '0');
    if (isNaN(amt) || amt < 0) {
        toast.error('Amount must be a non-negative number');
        return;
    }
    if (selectedMembers.length === 0) {
        toast.error('Select at least one member');
        return;
    }
        const response = await fetch(`${API}/createtransaction`, {
			method: 'POST',
            headers: authHeaders(),
			body: JSON.stringify({
				name: transactionName,
				tripid: location.state.tripid,
                amount: amt,
                member_ids: selectedMembers,
			}),
		});
		const json = await response.json();
		if (!json.success) {
			(json.errors || []).forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			console.log(json);
			if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
			navigate('/transaction', {
				state: {
					transactionid: json.transactionid,
					tripid: location.state.tripid,
				},
			});
		}
	};

	return (
		<div>
			<div style={{ position: 'relative' }}>
				<div
					style={{
						position: 'absolute',
						top: 0,
						left: 0,
						zIndex: 1,
						width: '100%',
					}}
				>
					<TransactionTable tripid={location.state.tripid} />
				</div>
				<div
					className='lol'
					style={{
						position: 'absolute',
						top: 0,
						left: 0,
						zIndex: 10,
						padding: '10px',
						display: 'flex',
						gap: '10px',
					}}
				>
					<Button onClick={handleOpen} variant='contained'>
						Create New Transaction
					</Button>
					<Button
						onClick={() =>
							navigate('/trip', {
								state: { tripid: location.state.tripid },
							})
						}
						variant='contained'
					>
						Back To Trip
					</Button>
				</div>
			</div>
			<Modal open={open} onClose={handleClose} aria-labelledby='modal-modal-title' aria-describedby='modal-modal-description'>
				<Box sx={style}>
					<form
						onSubmit={submitTransactionForm}
						style={{
							width: '100%',
							display: 'flex',
							flexDirection: 'column',
							alignItems: 'stretch',
							justifyContent: 'center',
							gap: '10px',
						}}
					>
						<TextField
							type='text'
							id='transactionName'
							value={transactionName}
							label='Transaction Name'
							onChange={e => setTransactionName(e.target.value)}
						/>
						<TextField
							type='number'
							id='amount'
							value={amount}
							label='Amount'
							onChange={e => setAmount(e.target.value)}
						/>
						<div style={{ width: '100%', maxHeight: '40vh', overflow: 'auto', border: '1px solid #ddd', padding: '8px' }}>
							<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
								<Typography variant='subtitle1'>Select Members</Typography>
								<Typography variant='body2'>
									{selectedMembers.length > 0 && !isNaN(parseFloat(amount || '0'))
										? `≈ ${((parseFloat(amount || '0') || 0) / Math.max(1, selectedMembers.length)).toFixed(2)} each`
										: ''}
								</Typography>
							</div>
							<FormGroup>
								{members.map(m => (
									<FormControlLabel
										key={m._id}
										control={<Checkbox checked={selectedMembers.includes(m._id)} onChange={() => toggleMember(m._id)} />}
										label={`${m.name} (${m.email})`}
									/>
								))}
							</FormGroup>
							<div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
								<Button variant='outlined' onClick={() => setSelectedMembers(members.map(m => m._id))}>
									Select All
								</Button>
								<Button variant='outlined' onClick={() => setSelectedMembers([])}>
									Clear
								</Button>
							</div>
						</div>
						<Button type='submit' variant='outlined'>
							Submit
						</Button>
					</form>
				</Box>
			</Modal>
		</div>
	);
}

export default Login;
